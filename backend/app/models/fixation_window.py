from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.dye_lot import DyeLot


class FixationWindow(Base):
    """固色静置窗：挂在染程上，actual_end_at 为空即进行中。"""

    __tablename__ = "fixation_windows"
    __table_args__ = (
        # 同一染程同时只允许一条未结束（actual_end_at IS NULL）的静置
        Index(
            "uq_active_fixation_per_lot",
            "dye_lot_id",
            unique=True,
            postgresql_where=text("actual_end_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dye_lot_id: Mapped[int] = mapped_column(ForeignKey("dye_lots.id"), nullable=False, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duty_officer: Mapped[str] = mapped_column(String(64), nullable=False)

    dye_lot: Mapped["DyeLot"] = relationship("DyeLot", back_populates="fixation_windows")

    @property
    def active(self) -> bool:
        return self.actual_end_at is None
