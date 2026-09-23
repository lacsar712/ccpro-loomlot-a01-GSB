from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.dye_lot import DyeLot


class FixationDwell(Base):
    """固色静置窗：染程挂起静置，未结束（actual_end 为空）即视为进行中。"""

    __tablename__ = "fixation_dwells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dye_lot_id: Mapped[int] = mapped_column(ForeignKey("dye_lots.id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duty_officer: Mapped[str] = mapped_column(String(64), nullable=False)

    dye_lot: Mapped["DyeLot"] = relationship("DyeLot", back_populates="fixation_dwells")

    @property
    def is_active(self) -> bool:
        """未写实际结束时刻即视为进行中。"""
        return self.actual_end_at is None

    @classmethod
    def active_query(cls, db, dye_lot_id: int):
        """进行中静置的唯一判定查询：拦截色牢度登记与新建静置共用。"""
        return db.query(cls).filter(
            cls.dye_lot_id == dye_lot_id,
            cls.actual_end_at.is_(None),
        )

    @classmethod
    def active_lot_ids(cls, db, lot_ids: Optional[List[int]] = None) -> set:
        """批量判定哪些染程正在静置，供列表行标记共用同一查询口径。"""
        q = db.query(cls.dye_lot_id).filter(cls.actual_end_at.is_(None))
        if lot_ids is not None:
            q = q.filter(cls.dye_lot_id.in_(lot_ids))
        return {row[0] for row in q.all()}
