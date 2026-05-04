from pydantic import BaseModel
from typing import Optional


class ProjectSchemaSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    schema: dict
    ui_schema: Optional[dict] = None
    data: Optional[dict] = None
