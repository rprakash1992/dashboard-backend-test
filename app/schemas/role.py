from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from enum import Enum
from uuid import UUID


class RoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: str
    action: str
    sections: Optional[List[str]] = None
    
    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class RoleAction(str, Enum):
    READ_ITEMS = "read_items"
    READ_METADATA = "read_metadata"
    READ_CONTENTS = "read_contents"
    UPDATE_METADATA = "update_metadata"
    UPDATE_CONTENTS = "update_contents"
    DELETE = "delete"
    CREATE = "create"
