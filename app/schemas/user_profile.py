from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, Optional
from enum import Enum
from uuid import UUID


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class UserProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    dob: Optional[datetime] = None
    picture: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[StatusEnum] = StatusEnum.PENDING
    gender: Optional[GenderEnum] = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class PutUserProfileSchema(BaseModel):
    id: str
    name: str
    email: str
    dob: Optional[datetime] = None
    picture: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    # status: Optional[StatusEnum] = StatusEnum.PENDING
    gender: Optional[GenderEnum] = None


class PatchUserProfileSchema(BaseModel):
    field_name: str
    field_value: Any
