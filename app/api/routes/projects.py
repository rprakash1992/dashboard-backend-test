from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
import json

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.project import InsertProjectResponse, ProjectSchema

# import services
from app.services.project import ProjectService


router = APIRouter()


class InsertProjectRequest(BaseModel):
    title: str
    file: str
    file_parameters: Optional[dict]
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateProjectFieldRequest(BaseModel):
    field_name: str
    field_value: Any


@router.get("/{selected_workspace_id}/projects", response_model=List[ProjectSchema])
async def fetch_projects_by_ids(
    selected_workspace_id: str,
    project_ids: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    project_ids = json.loads(project_ids)

    if not (selected_workspace_id and project_ids and len(project_ids) > 0):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    project_service = ProjectService(db)
    return project_service.fetch_projects_by_ids(
        loggedin_user_id, selected_workspace_id, project_ids
    )


@router.post("/{selected_workspace_id}/projects", response_model=InsertProjectResponse)
async def insert_project(
    selected_workspace_id: str,
    body: InsertProjectRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    title = body.title
    file = body.file
    file_parameters = body.file_parameters or {}
    description = body.description or ""
    image = body.image or ""
    tags = body.tags or []

    if not (selected_workspace_id and title and file and file_parameters):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    project_service = ProjectService(db)
    return project_service.insert_project(
        selected_workspace_id,
        loggedin_user_id,
        title,
        description,
        image,
        tags,
        file,
        file_parameters,
    )
