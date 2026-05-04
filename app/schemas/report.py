from pydantic import BaseModel, field_validator
from typing import Optional, Any
from uuid import UUID
from app.schemas.item import ItemSchema


class ReportSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    project: str
    template: Optional[str] = None
    data_values: Optional[dict] = None
    script: Optional[str] = None
    views: Optional[dict] = None

    @field_validator("id", "project", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class UpdateReportSchema(BaseModel):
    updatedFieldName: str
    updatedFieldValue: Any


class InsertReportResponse(BaseModel):
    item: ItemSchema
    report: ReportSchema
