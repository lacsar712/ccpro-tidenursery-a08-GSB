from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models.microscopy_batch import MicroscopyBatch
from app.models.microscopy_view import MicroscopyView
from app.models.pond import Pond
from app.models.user import User
from app.schemas.microscopy import (
    MicroscopyBatchCreate,
    MicroscopyBatchOut,
    MicroscopyViewCreate,
)

router = APIRouter(prefix="/api/microscopy-batches", tags=["microscopy"])


def _get_batch(db: Session, batch_id: int) -> MicroscopyBatch:
    batch = (
        db.query(MicroscopyBatch)
        .options(joinedload(MicroscopyBatch.views))
        .filter(MicroscopyBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="镜检批次不存在")
    return batch


@router.get("", response_model=List[MicroscopyBatchOut])
def list_batches(
    pond_id: Optional[int] = Query(None, alias="pondId"),
    sealed: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(MicroscopyBatch).options(joinedload(MicroscopyBatch.views))
    if pond_id is not None:
        q = q.filter(MicroscopyBatch.pond_id == pond_id)
    if sealed is True:
        q = q.filter(MicroscopyBatch.sealed_at.is_not(None))
    elif sealed is False:
        q = q.filter(MicroscopyBatch.sealed_at.is_(None))
    return q.order_by(MicroscopyBatch.inspected_on.desc(), MicroscopyBatch.id.desc()).all()


@router.post("", response_model=MicroscopyBatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: MicroscopyBatchCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pond = db.query(Pond).filter(Pond.id == payload.pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    batch = MicroscopyBatch(
        pond_id=payload.pond_id,
        inspected_on=payload.inspected_on,
        sealed_at=None,
        chief_inspector=payload.chief_inspector,
    )
    db.add(batch)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该塘口当日（东八区）已有镜检批次")
    db.refresh(batch)
    return _get_batch(db, batch.id)


@router.get("/{batch_id}", response_model=MicroscopyBatchOut)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _get_batch(db, batch_id)


@router.post(
    "/{batch_id}/views",
    response_model=MicroscopyBatchOut,
    status_code=status.HTTP_201_CREATED,
)
def add_view(
    batch_id: int,
    payload: MicroscopyViewCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    batch = _get_batch(db, batch_id)
    if batch.sealed_at is not None:
        raise HTTPException(status_code=409, detail="批次已封检，不可再追加视野")
    view = MicroscopyView(
        batch_id=batch.id,
        view_no=payload.view_no,
        floc_density=payload.floc_density,
        observed_at=payload.observed_at,
    )
    db.add(view)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="视野序号在本批次内已存在")
    return _get_batch(db, batch.id)


@router.post("/{batch_id}/seal", response_model=MicroscopyBatchOut)
def seal_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    batch = _get_batch(db, batch_id)
    if batch.sealed_at is not None:
        return batch
    # 封检规则：至少三个视野，且不得全为密
    if len(batch.views) < 3:
        raise HTTPException(status_code=409, detail="封检失败：至少需要 3 个视野")
    if all(v.floc_density == "dense" for v in batch.views):
        raise HTTPException(status_code=409, detail="封检失败：视野絮团密度不得全为「密」")
    batch.sealed_at = datetime.now(timezone.utc)
    db.commit()
    return _get_batch(db, batch.id)
