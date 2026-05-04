from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from enum import Enum


class RelationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_id: str
    target_id: str
    relation: str

    @field_validator("source_id", "target_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class RelationType(str, Enum):
    DEPENDENT = "dependent"
    CHILD = "child"
    JOB = "job"
    JOB_OUTPUT = "job_output"
    ROLE = "role"
