from pydantic import BaseModel
from typing import Optional


class UserFlowSchema(BaseModel):
    id: str
    s3_key: str
    flow_function_name: str
    deployment_id: str
    deployment_name: str
    flow_id: str
    parameter_schema: Optional[dict] = None


# class TriggerFlowRunSchema(BaseModel):
#     parameters: Optional[Dict[str, Any]] = None
