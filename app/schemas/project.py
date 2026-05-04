from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from app.schemas.item import ItemSchema


class ProjectSchema(BaseModel):
    model_config = {"from_attributes": True}

    project: str
    file: str
    file_parameters: Optional[dict] = None
    
    @field_validator("project", "file", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class InsertProjectResponse(BaseModel):
    item: ItemSchema
    project: ProjectSchema
