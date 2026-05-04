from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
import json

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.job import InsertJobResponse, JobResponseSchema

# import services
from app.services.job import JobService


router = APIRouter()


class InsertJobRequest(BaseModel):
    title: str
    workflow_id: str
    workflow_parameters: Optional[dict] = None
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateJobFieldRequest(BaseModel):
    field_name: str
    field_value: Any


@router.get("/{selected_workspace_id}/jobs")
async def fetch_jobs_by_ids(
    selected_workspace_id: str,
    job_ids: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    job_ids = json.loads(job_ids)

    if not (selected_workspace_id and job_ids and len(job_ids) > 0):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    job_service = JobService(db)
    return await job_service.fetch_jobs_by_ids(
        selected_workspace_id, loggedin_user_id, job_ids
    )


@router.get(
    "/{selected_workspace_id}/jobs/output-items", response_model=List[JobResponseSchema]
)
async def fetch_jobs_by_output_item_ids(
    selected_workspace_id: str,
    output_items_ids: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    output_items_ids = json.loads(output_items_ids)

    if not (selected_workspace_id and output_items_ids and len(output_items_ids) > 0):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    response = []
    job_service = JobService(db)
    for id in output_items_ids:
        resp = await job_service.get_job_by_output_item_id(
            selected_workspace_id, loggedin_user_id, id
        )
        if resp:
            response.append(resp)
    return response


@router.post("/{selected_workspace_id}/jobs", response_model=InsertJobResponse)
async def create_job_from_workflow(
    selected_workspace_id: str,
    body: InsertJobRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    title = body.title
    workflow_id = body.workflow_id
    workflow_parameters = body.workflow_parameters
    description = body.description or ""
    image = body.image or ""
    tags = body.tags or []

    if not (selected_workspace_id and title and workflow_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    job_service = JobService(db)
    return await job_service.create_job_from_workflow(
        selected_workspace_id,
        loggedin_user_id,
        title,
        description,
        image,
        tags,
        workflow_id,
        workflow_parameters,
    )
