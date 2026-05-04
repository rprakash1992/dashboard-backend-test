from pydantic import BaseModel
from typing import Optional, List, Any


class FileSchema(BaseModel):
    id: Optional[str] = None
    lastModified: int | str
    name: str
    size: int | str


class ResponseStatus(BaseModel):
    success: bool
    errorMessage: str


class Checksum(BaseModel):
    method: str


class InitiateFileUploadResponseSchema(BaseModel):
    file: Optional[FileSchema] = None
    checksum: Optional[Checksum] = None
    status: ResponseStatus


class UpdateFilePartUrlsResponseSchema(BaseModel):
    parts: List[Any]
    status: ResponseStatus


class UpdateFilePartsStatusResponseSchema(BaseModel):
    status: ResponseStatus
    parts: Optional[List[Any]] = None
    upload_complete: Optional[bool] = False


class UploadItemSchema(BaseModel):
    id: str
    file_name: str
    file_size: int
    file_last_modified: int
    s3: dict
    checksum: Checksum
    parts: List[dict]


# class InitiateFileUploadRequest(BaseModel):
#     name: str
#     size: int
#     lastModified: int
