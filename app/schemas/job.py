from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from enum import Enum
from uuid import UUID
from app.schemas.item import ItemSchema


class JobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    job_type: str
    total_steps: Optional[int] = None
    completed_steps: Optional[int] = None
    run_id: Optional[str] = None
    
    @field_validator("id", "run_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    
class JobResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    job_type: str
    total_steps: Optional[int] = None
    completed_steps: Optional[int] = None
    run_id: Optional[str] = None
    run_details: Optional[dict] = None
    output_item_id: Optional[str] = None
    
    @field_validator("id", "run_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class InsertJobResponse(BaseModel):
    item: ItemSchema
    job: JobSchema


class JobType(str, Enum):
    WORKFLOW_RUN = "workflow_run"
    ZIP_TO_FOLDER = "zip_to_folder"
    FOLDER_TO_ZIP = "folder_to_zip"
    ZIP_TO_WORKFLOW = "zip_to_workflow"
