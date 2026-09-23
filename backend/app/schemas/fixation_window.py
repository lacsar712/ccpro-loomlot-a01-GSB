from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FixationWindowCreate(BaseModel):
    dye_lot_id: int = Field(..., alias="dyeLotId")
    start_at: datetime = Field(..., alias="startAt")
    planned_end_at: datetime = Field(..., alias="plannedEndAt")
    duty_officer: str = Field(..., min_length=1, max_length=64, alias="dutyOfficer")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def _check_planned_after_start(self):
        if self.planned_end_at <= self.start_at:
            raise ValueError("计划结束时刻必须晚于开始时刻")
        return self


class FixationWindowFinish(BaseModel):
    actual_end_at: datetime = Field(..., alias="actualEndAt")

    model_config = ConfigDict(populate_by_name=True)


class FixationWindowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    dye_lot_id: int = Field(serialization_alias="dyeLotId")
    start_at: datetime = Field(serialization_alias="startAt")
    planned_end_at: datetime = Field(serialization_alias="plannedEndAt")
    actual_end_at: Optional[datetime] = Field(None, serialization_alias="actualEndAt")
    duty_officer: str = Field(serialization_alias="dutyOfficer")
    active: bool
