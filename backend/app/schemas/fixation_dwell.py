from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field


class FixationDwellCreate(BaseModel):
    dye_lot_id: int = Field(..., alias="dyeLotId")
    started_at: datetime = Field(..., alias="startedAt")
    planned_end_at: datetime = Field(..., alias="plannedEndAt")
    duty_officer: str = Field(..., min_length=1, max_length=64, alias="dutyOfficer")

    model_config = ConfigDict(populate_by_name=True)


class FixationDwellEnd(BaseModel):
    actual_end_at: datetime = Field(..., alias="actualEndAt")

    model_config = ConfigDict(populate_by_name=True)


class FixationDwellOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    dye_lot_id: int = Field(serialization_alias="dyeLotId")
    started_at: datetime = Field(serialization_alias="startedAt")
    planned_end_at: datetime = Field(serialization_alias="plannedEndAt")
    actual_end_at: Optional[datetime] = Field(default=None, serialization_alias="actualEndAt")
    duty_officer: str = Field(serialization_alias="dutyOfficer")

    @computed_field(alias="active")
    @property
    def active(self) -> bool:
        return self.actual_end_at is None
