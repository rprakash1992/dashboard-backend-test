from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
import json

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.workflow import WorkflowSchema, InsertWorkflowResponse

# import services
from app.services.workflow import WorkflowService


router = APIRouter()


class InsertWorkflowRequest(BaseModel):
    title: str
    file_id: str
    variables: Optional[dict] = None
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateReportFieldRequest(BaseModel):
    field_name: str
    field_value: Any


@router.get("/{selected_workspace_id}/workflows", response_model=List[WorkflowSchema])
async def fetch_workflows_by_ids(
    selected_workspace_id: str,
    workflow_ids: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    workflow_ids = json.loads(workflow_ids)

    if not (selected_workspace_id and workflow_ids and len(workflow_ids) > 0):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    workflow_service = WorkflowService(db)
    return workflow_service.fetch_workflows_by_ids(
        selected_workspace_id, loggedin_user_id, workflow_ids
    )


@router.post(
    "/{selected_workspace_id}/workflows", response_model=InsertWorkflowResponse
)
async def create_workflow(
    selected_workspace_id: str,
    body: InsertWorkflowRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    title = body.title
    file_id = body.file_id
    variables = body.variables or {}
    description = body.description or ""
    image = body.image or ""
    tags = body.tags or []

    if not (selected_workspace_id and title and file_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    workflow_service = WorkflowService(db)
    return await workflow_service.create_workflow(
        selected_workspace_id,
        loggedin_user_id,
        title,
        description,
        image,
        tags,
        file_id,
        variables,
    )
