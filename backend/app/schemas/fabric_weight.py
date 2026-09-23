from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FabricWeightRecordCreate(BaseModel):
    dye_lot_id: int = Field(..., alias="dyeLotId")
    weighed_at: datetime = Field(..., alias="weighedAt")
    weight_kg: float = Field(..., gt=0, alias="weightKg")
    recorder_name: str = Field(..., min_length=1, max_length=64, alias="recorderName")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class FabricWeightRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    dye_lot_id: int = Field(serialization_alias="dyeLotId")
    weighed_at: datetime = Field(serialization_alias="weighedAt")
    weight_kg: float = Field(serialization_alias="weightKg")
    recorder_name: str = Field(serialization_alias="recorderName")
    notes: Optional[str] = None
