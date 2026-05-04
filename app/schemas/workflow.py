from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from app.schemas.item import ItemSchema


class WorkflowSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    s3_key: Optional[str] = None
    flow_function_name: Optional[str] = None
    deployment_id: Optional[str] = None
    deployment_name: Optional[str] = None
    flow_id: Optional[str] = None
    status: Optional[str] = None
    is_valid: Optional[bool] = None
    parameter_schema: Optional[dict] = None
    
    @field_validator("id", "deployment_id", "flow_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class InsertWorkflowResponse(BaseModel):
    item: ItemSchema
    workflow: WorkflowSchema
