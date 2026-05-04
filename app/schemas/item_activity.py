from pydantic import BaseModel
from typing import Optional


class ItemActivitySchema(BaseModel):
    id: int
    item_id: str
    user_id: str
    prev_action: Optional[int] = None
    timestamp: Optional[str] = None
    activity_type: Optional[str] = None
    content: Optional[str] = None
