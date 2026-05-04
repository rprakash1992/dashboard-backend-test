from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, List, Optional, Union
from enum import Enum


class ItemType(str, Enum):
    FILE = "file"
    PROJECT = "project"
    REPORT = "report"
    WORKSPACE = "workspace"
    USERPROFILE = "user_profile"
    ROLE = "role"
    JOB = "job"
    WORKFLOW = "workflow"


class UpdateItemSchema(BaseModel):
    field_name: str
    field_value: Any


class ItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    item_type: ItemType
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    last_modified_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    system_key: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class NewItemSchema(BaseModel):
    title: str
    item_type: ItemType
    description: Optional[str] = None
    image: Optional[str] = None
    tags: List[str] = None


class FileTraceabilityData(BaseModel):
    projects: List[ItemSchema]


class ProjectTraceabilityData(BaseModel):
    files: List[ItemSchema]
    reports: List[ItemSchema]


class ReportTraceabilityData(BaseModel):
    projects: List[ItemSchema]


class JobTraceabilityData(BaseModel):
    inputs: List[ItemSchema]
    outputs: List[ItemSchema]


class WorkflowTraceabilityData(BaseModel):
    inputs: List[ItemSchema]
    outputs: List[ItemSchema]


class TraceabilityRespSchema(BaseModel):
    item_type: ItemType
    traceability_data: Union[
        FileTraceabilityData,
        ProjectTraceabilityData,
        ReportTraceabilityData,
        JobTraceabilityData,
        WorkflowTraceabilityData,
    ]
