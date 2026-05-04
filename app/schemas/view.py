from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List, Any
from enum import Enum


class ViewAsEnum(str, Enum):
    GRID = "grid"
    TABLE = "table"


class ViewStatusEnum(str, Enum):
    PERMANENT = "permanent"
    PINNED = "pinned"


class FilterSchema(BaseModel):
    id: str
    filterTitle: str
    operator: str
    value: Any
    isChecked: Optional[bool] = True


class FilterGroupSchema(BaseModel):
    id: str
    filterTitle: str
    operator: str
    children: List[FilterSchema]
    groupOperator: str
    isChecked: Optional[bool] = True


class FiltersSchema(BaseModel):
    filterType: Optional[List[FilterSchema]] = []
    groupedFilterType: Optional[List[FilterGroupSchema]] = []


class ViewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    owner: Optional[UUID4] = None
    item_type: str
    view_as: Optional[ViewAsEnum] = ViewAsEnum.GRID.value
    filters: Optional[FiltersSchema] = None
    group_by: str
    sort_by: str
    status: Optional[str] = ViewStatusEnum.PERMANENT.value


class CreateViewSchema(BaseModel):
    title: str
    item_type: str
    view_as: Optional[ViewAsEnum] = ViewAsEnum.GRID.value
    filters: Optional[FiltersSchema] = None
    group_by: str
    sort_by: str
    status: Optional[ViewStatusEnum] = ViewStatusEnum.PINNED.value


class PatchViewSchema(BaseModel):
    field_name: str
    field_value: Any
