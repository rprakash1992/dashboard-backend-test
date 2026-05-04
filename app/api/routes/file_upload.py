from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Any
import boto3
from pydantic import BaseModel
from decimal import Decimal

# import core
from app.core.config import get_settings
# from app.core.dashboard_database import get_dashboard_db
from app.core.sqlite_database import get_sqlite_db
# from app.core.prefect_database import get_prefect_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.file_upload import (
    UpdateFilePartsStatusResponseSchema,
    UpdateFilePartUrlsResponseSchema,
    InitiateFileUploadResponseSchema,
    ResponseStatus,
    FileSchema,
)

# import services
from app.services.file_upload import FileUploadService

# import utils
from app.utils.misc import get_parsed_data


settings = get_settings()

aws_s3_bucket = settings.aws_s3_bucket
aws_access_key = settings.aws_access_key
aws_secret_key = settings.aws_secret_key
aws_region = settings.aws_region


class InitiateFileUploadRequest(BaseModel):
    file: FileSchema
    file_s3_url: str


class FileIdSchema(BaseModel):
    id: str


class UpdateFilePartsUrlRequest(BaseModel):
    file: FileIdSchema


class UpdateFilePartsStatusRequest(BaseModel):
    id: str
    parts: List[Any]
    estimatedTime: Decimal


router = APIRouter()


@router.post(
    "/file-upload/initiate-file-upload", response_model=InitiateFileUploadResponseSchema
)
async def initiate_file_upload(
    body: InitiateFileUploadRequest,
    db: Session = Depends(get_sqlite_db),
    # dashboard_db=Depends(get_dashboard_db),
    # prefect_db: Session = Depends(get_prefect_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    file_upload_service = FileUploadService(
        # dashboard_db,
        # prefect_db
    )
    initiated_file_upload = await file_upload_service.initiate_file_upload(
        body.file_s3_url, body.file.name, body.file.size, body.file.lastModified, db
    )

    response_status = ResponseStatus(success=True, errorMessage="")

    return InitiateFileUploadResponseSchema(
        file=initiated_file_upload.file,
        checksum=initiated_file_upload.checksum,
        status=response_status,
    )


@router.post(
    "/file-upload/update-file-part-urls",
    response_model=UpdateFilePartUrlsResponseSchema,
)
async def update_file_part_urls(
    body: UpdateFilePartsUrlRequest,
    db: Session = Depends(get_sqlite_db),
    # dashboard_db=Depends(get_dashboard_db),
    # prefect_db: Session = Depends(get_prefect_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    file_upload_service = FileUploadService(
        # dashboard_db,
        # prefect_db
    )
    return await file_upload_service.update_file_part_urls(body.file.id, db)


@router.post(
    "/file-upload/update-file-parts-status",
    response_model=UpdateFilePartsStatusResponseSchema,
)
async def update_file_part_status(
    body: UpdateFilePartsStatusRequest,
    db: Session = Depends(get_sqlite_db),
    # dashboard_db=Depends(get_dashboard_db),
    # prefect_db: Session = Depends(get_prefect_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    file_upload_service = FileUploadService(
        # dashboard_db,
        # prefect_db
    )
    return await file_upload_service.update_file_parts_status(
        body.id, body.parts, int(body.estimatedTime), db
    )


# @router.post("/{selected_workspace_id}/file/{item_id}/extract-zip")
# async def extract_zip(
#     selected_workspace_id: str,
#     item_id: str,
#     db: Session = Depends(get_dashboard_db),
#     prefect_db: Session = Depends(get_prefect_db),
#     loggedin_user_id: str = Depends(get_current_user_id),
# ):
#     file_upload_service = FileUploadService(db, prefect_db)
#     return await file_upload_service.extract_zip_prefect(
#         selected_workspace_id,
#         loggedin_user_id,
#         item_id,
#     )


# @router.post("/{selected_workspace_id}/file/{item_id}/compress-file")
# async def compress_file(
#     selected_workspace_id: str,
#     item_id: str,
#     db: Session = Depends(get_dashboard_db),
#     prefect_db: Session = Depends(get_prefect_db),
#     loggedin_user_id: str = Depends(get_current_user_id),
# ):
#     file_upload_service = FileUploadService(db, prefect_db)
#     return await file_upload_service.compress_file_prefect(
#         selected_workspace_id, loggedin_user_id, item_id
#     )


@router.post("/file-upload/get-image-upload-url")
async def get_image_upload_url(
    request: Request,
    loggedin_user_id: str = Depends(get_current_user_id),
):
    parsed_data = await get_parsed_data(request)
    # folder_name = parsed_data.get("folderName")
    file_key = parsed_data.get("fileKey")
    content_type = parsed_data.get("contentType", "application/octet-stream")
    key = file_key

    client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name="us-east-1",
        config=boto3.session.Config(signature_version="s3v4"),
    )

    presigned_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": aws_s3_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=3600,
    )
    
    return presigned_url

    # return {
    #     "error": None,
    #     "data": presigned_url,
    # }


@router.post("/file-upload/get-image-download-url")
async def get_image_download_url(
    request: Request,
    loggedin_user_id: str = Depends(get_current_user_id),
):
    parsed_data = await get_parsed_data(request)
    file_key = parsed_data.get("fileKey")

    if not file_key:
        return ""

    client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name="us-east-1",
        config=boto3.session.Config(signature_version="s3v4"),
    )

    presigned_url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": aws_s3_bucket,
            "Key": file_key,
        },
        ExpiresIn=3600,
    )

    return presigned_url


@router.post("/file-upload/get-image-download-urls")
async def get_image_download_urls(
    request: Request,
    loggedin_user_id: str = Depends(get_current_user_id),
):
    parsed_data = await get_parsed_data(request)
    file_keys: List[str] = parsed_data.get("fileKeys", [])

    client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name="us-east-1",
        config=boto3.session.Config(signature_version="s3v4"),
    )

    presigned_urls = [
        client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": aws_s3_bucket,
                "Key": key,
            },
            ExpiresIn=3600,
        ) if key else ""
        for key in file_keys
    ]

    return presigned_urls
