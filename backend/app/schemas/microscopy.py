from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DensityLevel = Literal["sparse", "medium", "dense"]


class MicroscopyBatchCreate(BaseModel):
    pond_id: int = Field(..., alias="pondId")
    opened_on: date = Field(..., alias="openedOn")
    chief_inspector: str = Field(..., min_length=1, max_length=64, alias="chiefInspector")

    model_config = ConfigDict(populate_by_name=True)


class MicroscopyFieldCreate(BaseModel):
    view_seq: int = Field(..., ge=1, alias="viewSeq")
    density: DensityLevel
    observed_at: datetime = Field(..., alias="observedAt")

    model_config = ConfigDict(populate_by_name=True)


class MicroscopyFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    batch_id: int = Field(serialization_alias="batchId")
    view_seq: int = Field(serialization_alias="viewSeq")
    density: DensityLevel
    observed_at: datetime = Field(serialization_alias="observedAt")


class MicroscopyBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    pond_id: int = Field(serialization_alias="pondId")
    opened_on: date = Field(serialization_alias="openedOn")
    closed_at: Optional[datetime] = Field(serialization_alias="closedAt")
    chief_inspector: str = Field(serialization_alias="chiefInspector")
    fields: List[MicroscopyFieldOut] = []
