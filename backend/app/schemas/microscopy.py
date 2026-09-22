from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

FlocDensity = Literal["sparse", "medium", "dense"]


class MicroscopyBatchCreate(BaseModel):
    pond_id: int = Field(..., alias="pondId")
    inspected_on: date = Field(..., alias="inspectedOn")
    chief_inspector: str = Field(..., min_length=1, max_length=64, alias="chiefInspector")

    model_config = ConfigDict(populate_by_name=True)


class MicroscopyViewCreate(BaseModel):
    view_no: int = Field(..., ge=1, alias="viewNo")
    floc_density: FlocDensity = Field(..., alias="flocDensity")
    observed_at: datetime = Field(..., alias="observedAt")

    model_config = ConfigDict(populate_by_name=True)


class MicroscopyViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    view_no: int = Field(serialization_alias="viewNo")
    floc_density: FlocDensity = Field(serialization_alias="flocDensity")
    observed_at: datetime = Field(serialization_alias="observedAt")


class MicroscopyBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    pond_id: int = Field(serialization_alias="pondId")
    inspected_on: date = Field(serialization_alias="inspectedOn")
    sealed_at: Optional[datetime] = Field(None, serialization_alias="sealedAt")
    chief_inspector: str = Field(serialization_alias="chiefInspector")
    views: List[MicroscopyViewOut] = []
