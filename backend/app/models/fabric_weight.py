from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.dye_lot import DyeLot


class FabricWeight(Base):
    """布重千克记录：静置结束对账用，要求同染程至少已有一条。"""

    __tablename__ = "fabric_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dye_lot_id: Mapped[int] = mapped_column(ForeignKey("dye_lots.id"), nullable=False, index=True)
    weighed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    recorder_name: Mapped[str] = mapped_column(String(64), nullable=False)

    dye_lot: Mapped["DyeLot"] = relationship("DyeLot", back_populates="fabric_weights")
