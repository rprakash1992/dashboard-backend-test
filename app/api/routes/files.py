from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
import json

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.file import FileSchema, InsertFileResponse

# import services
from app.services.file import FileService


router = APIRouter()


class InsertFileRequest(BaseModel):
    title: str
    file_extension: str
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateFileFieldRequest(BaseModel):
    field_name: str
    field_value: Any


@router.get("/{selected_workspace_id}/files", response_model=List[FileSchema])
async def fetch_files_by_ids(
    selected_workspace_id: str,
    file_ids: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    # prefect_db: Session = Depends(get_prefect_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    file_ids = json.loads(file_ids)

    if not (selected_workspace_id and file_ids and len(file_ids) > 0):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    file_service = FileService(
        db,
        # prefect_db
    )
    return file_service.fetch_files_by_ids(
        selected_workspace_id, loggedin_user_id, file_ids
    )


@router.get("/{selected_workspace_id}/files/{item_id}/copy/{item_id_to}")
async def copy_item_to_another_folder(
    selected_workspace_id: str,
    item_id: str,
    item_id_to: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (selected_workspace_id and item_id and item_id_to):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    file_service = FileService(db)
    return file_service.copy_item_to_another_folder(
        selected_workspace_id, loggedin_user_id, item_id, item_id_to
    )


@router.get("/{selected_workspace_id}/files/{file_id}/download", response_model=str)
async def download_file_endpoint(
    selected_workspace_id: str,
    file_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (selected_workspace_id and file_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    file_service = FileService(db)
    return file_service.download_file(selected_workspace_id, loggedin_user_id, file_id)


@router.post("/{selected_workspace_id}/files", response_model=InsertFileResponse)
async def insert_file(
    selected_workspace_id: str,
    body: InsertFileRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    title = body.title
    file_extension = body.file_extension
    description = body.description or ""
    image = body.image or ""
    tags = body.tags or []

    if not (selected_workspace_id and title and file_extension):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    file_service = FileService(db)
    return file_service.insert_file(
        selected_workspace_id,
        loggedin_user_id,
        title,
        description,
        image,
        tags,
        file_extension,
    )


@router.post("/{selected_workspace_id}/files/{item_id}/extract")
async def extract_zip(
    selected_workspace_id: str,
    item_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    file_upload_service = FileService(db)
    return await file_upload_service.extract_zip_prefect(
        selected_workspace_id,
        loggedin_user_id,
        item_id,
    )


@router.post("/{selected_workspace_id}/files/{item_id}/compress")
async def compress_file(
    selected_workspace_id: str,
    item_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    file_upload_service = FileService(db)
    return await file_upload_service.compress_file_prefect(
        selected_workspace_id, loggedin_user_id, item_id
    )


@router.patch(
    "/{selected_workspace_id}/files/{file_id}",
    response_model=FileSchema,
)
async def update_file_field(
    selected_workspace_id: str,
    file_id: str,
    body: UpdateFileFieldRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    field_name = body.field_name
    field_value = body.field_value

    if not (selected_workspace_id and file_id and field_name):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    file_service = FileService(db)
    return file_service.update_file_field_by_id(
        selected_workspace_id, loggedin_user_id, file_id, field_name, field_value
    )
