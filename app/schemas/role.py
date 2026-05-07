from pydantic import BaseModel, ConfigDict, field_validator
from typing import List
from uuid import UUID
from app.schemas.item import ItemSchema


class RoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: str
    scope: str
    field: str
    can_create: bool = False
    can_read: bool = False
    can_update: bool = False
    can_delete: bool = False

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class NewRoleSchema(BaseModel):
    item_type: str
    scope: str
    field: str
    can_create: bool = False
    can_read: bool = False
    can_update: bool = False
    can_delete: bool = False


class RoleScope(str):
    METADATA = "metadata"
    CONTENT = "content"


class InsertRoleResponse(BaseModel):
    item: ItemSchema
    role: List[RoleSchema]
