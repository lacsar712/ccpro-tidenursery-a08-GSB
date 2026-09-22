from typing import Iterable, Optional, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.microscopy_batch import MicroscopyBatch


def open_batch_pond_ids(db: Session, pond_ids: Optional[Iterable[int]] = None) -> Set[int]:
    """存在未封检镜检批次的塘口编号集合。

    投喂拦截与塘口列表的未封标记共用本查询。
    """
    stmt = select(MicroscopyBatch.pond_id).where(MicroscopyBatch.sealed_at.is_(None))
    if pond_ids is not None:
        ids = list(pond_ids)
        if not ids:
            return set()
        stmt = stmt.where(MicroscopyBatch.pond_id.in_(ids))
    return {row[0] for row in db.execute(stmt).all()}


def pond_has_open_batch(db: Session, pond_id: int) -> bool:
    return pond_id in open_batch_pond_ids(db, [pond_id])
