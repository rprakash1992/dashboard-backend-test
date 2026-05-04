from pydantic import BaseModel, UUID4, ConfigDict, field_validator
from typing import Optional, Any
from uuid import UUID
from app.schemas.item import ItemSchema


class FileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    downloader_type: Optional[str] = None
    downloader_args: Optional[dict] = None
    cache_state: Optional[str] = None
    local_cache_file_path: Optional[str] = None
    mime_type: Optional[str] = None
    is_uploaded: bool
    parent: Optional[UUID4] = None
    
    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class NewFileSchema(BaseModel):
    url: str
    downloader_type: Optional[str] = None
    downloader_args: Optional[dict] = None
    cache_state: Optional[str] = None
    local_cache_file_path: Optional[str] = None
    mime_type: Optional[str] = None
    is_uploaded: bool
    parent: Optional[UUID4] = None


class InsertFileResponse(BaseModel):
    item: ItemSchema
    file: FileSchema
