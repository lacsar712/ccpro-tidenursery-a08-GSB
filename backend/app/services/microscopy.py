"""生物絮团镜检共享查询：投喂拦截与塘口未封标记共用同一查询口径。

开检日按东八区（CN_TZ）计算，种子与需要服务端取日的场景共用此时区定义。
"""
from datetime import timedelta, timezone
from typing import Iterable, Set

from sqlalchemy.orm import Session

from app.models.microscopy import MicroscopyBatch

# 开检日统一按东八区计算
CN_TZ = timezone(timedelta(hours=8))


def pond_ids_with_open_batch(db: Session, pond_ids: Iterable[int]) -> Set[int]:
    """在给定塘口候选中，返回存在未封检批次（closed_at 为空）的塘口 id 集合。

    投喂拦截与塘口列表「未封镜检」标记共用此查询口径。
    """
    ids = list(pond_ids)
    if not ids:
        return set()
    rows = (
        db.query(MicroscopyBatch.pond_id)
        .filter(MicroscopyBatch.closed_at.is_(None), MicroscopyBatch.pond_id.in_(ids))
        .distinct()
        .all()
    )
    return {row[0] for row in rows}
