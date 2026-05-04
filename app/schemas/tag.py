from pydantic import BaseModel, ConfigDict
from typing import Optional


class TagSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None


class CreateTagSchema(BaseModel):
    name: str
    description: Optional[str] = None
