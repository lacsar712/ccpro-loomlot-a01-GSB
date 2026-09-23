"""固色静置相关的共用查询。

拦截色牢度抽检与"是否静置中"判定必须共用同一查询，避免两处口径漂移。
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.fixation_window import FixationWindow


def get_active_window(db: Session, dye_lot_id: int) -> Optional[FixationWindow]:
    """返回该染程当前进行中（未写实际结束）的静置；没有则 None。"""
    return (
        db.query(FixationWindow)
        .filter(
            FixationWindow.dye_lot_id == dye_lot_id,
            FixationWindow.actual_end_at.is_(None),
        )
        .first()
    )


def as_utc(dt: datetime) -> datetime:
    """无时区信息的时间按 UTC 处理，保证 naive/aware 可安全比较。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
