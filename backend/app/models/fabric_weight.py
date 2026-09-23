from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.dye_lot import DyeLot


class FabricWeightRecord(Base):
    """布重（千克）记录：染程对账依据，结束固色静置前至少要有一条。"""

    __tablename__ = "fabric_weight_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dye_lot_id: Mapped[int] = mapped_column(ForeignKey("dye_lots.id"), nullable=False, index=True)
    weighed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    recorder_name: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    dye_lot: Mapped["DyeLot"] = relationship("DyeLot", back_populates="fabric_weights")
