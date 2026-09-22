from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.microscopy import MicroscopyBatch
from app.models.pond import Pond
from app.models.user import User
from app.schemas.microscopy import (
    MicroscopyBatchCreate,
    MicroscopyBatchOut,
    MicroscopyFieldCreate,
    MicroscopyFieldOut,
)

router = APIRouter(prefix="/api/microscopy-batches", tags=["microscopy"])

# 封检规则：至少三个视野，且不得全是密
MIN_FIELDS_TO_CLOSE = 3


@router.get("", response_model=List[MicroscopyBatchOut])
def list_batches(
    pond_id: Optional[int] = Query(None, alias="pondId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(MicroscopyBatch)
    if pond_id is not None:
        q = q.filter(MicroscopyBatch.pond_id == pond_id)
    return q.order_by(MicroscopyBatch.opened_on.desc(), MicroscopyBatch.id.desc()).all()


@router.get("/{batch_id}", response_model=MicroscopyBatchOut)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(MicroscopyBatch).filter(MicroscopyBatch.id == batch_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="镜检批次不存在")
    return item


@router.post("", response_model=MicroscopyBatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: MicroscopyBatchCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pond = db.query(Pond).filter(Pond.id == payload.pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    item = MicroscopyBatch(
        pond_id=payload.pond_id,
        opened_on=payload.opened_on,
        closed_at=None,
        chief_inspector=payload.chief_inspector,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该塘口当日已开过镜检批次")
    db.refresh(item)
    return item


@router.post(
    "/{batch_id}/fields",
    response_model=MicroscopyFieldOut,
    status_code=status.HTTP_201_CREATED,
)
def add_field(
    batch_id: int,
    payload: MicroscopyFieldCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    batch = db.query(MicroscopyBatch).filter(MicroscopyBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="镜检批次不存在")
    if batch.closed_at is not None:
        raise HTTPException(status_code=409, detail="批次已封检，不可再追加视野")
    item = MicroscopyField(
        batch_id=batch_id,
        view_seq=payload.view_seq,
        density=payload.density,
        observed_at=payload.observed_at,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该批次内视野序号已存在")
    db.refresh(item)
    return item


@router.post("/{batch_id}/close", response_model=MicroscopyBatchOut)
def close_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    batch = db.query(MicroscopyBatch).filter(MicroscopyBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="镜检批次不存在")
    if batch.closed_at is not None:
        raise HTTPException(status_code=409, detail="批次已封检")

    fields = batch.fields
    if len(fields) < MIN_FIELDS_TO_CLOSE:
        raise HTTPException(
            status_code=409,
            detail=f"封检失败：至少需要 {MIN_FIELDS_TO_CLOSE} 个视野，当前 {len(fields)} 个",
        )
    if all(f.density == "dense" for f in fields):
        raise HTTPException(status_code=409, detail="封检失败：视野密度不得全为密")

    batch.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(batch)
    return batch
