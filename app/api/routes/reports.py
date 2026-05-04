from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
import json

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.report import ReportSchema, InsertReportResponse

# import services
from app.services.report import ReportService


router = APIRouter()


class InsertReportRequest(BaseModel):
    title: str
    project: str
    template: str
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateReportFieldRequest(BaseModel):
    field_name: str
    field_value: Any


@router.get("/{selected_workspace_id}/reports", response_model=List[ReportSchema])
async def fetch_reports_by_ids(
    selected_workspace_id: str,
    report_ids: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    report_ids = json.loads(report_ids)

    if not (selected_workspace_id and report_ids and len(report_ids) > 0):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    report_service = ReportService(db)
    return report_service.fetch_reports_by_ids(
        loggedin_user_id, selected_workspace_id, report_ids
    )


@router.post("/{selected_workspace_id}/reports", response_model=InsertReportResponse)
async def insert_report(
    selected_workspace_id: str,
    body: InsertReportRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    title = body.title
    project = body.project
    template = body.template
    description = body.description or ""
    image = body.image or ""
    tags = body.tags or []

    if not (selected_workspace_id and title and project and template):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    report_service = ReportService(db)
    return report_service.insert_report(
        selected_workspace_id,
        loggedin_user_id,
        title,
        description,
        image,
        tags,
        project,
        template,
    )


@router.patch(
    "/{selected_workspace_id}/reports/{report_id}",
    response_model=ReportSchema,
)
async def update_report_endpoint(
    selected_workspace_id: str,
    report_id: str,
    body: UpdateReportFieldRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    field_name = body.field_name
    field_value = body.field_value

    if not (selected_workspace_id and report_id and field_name):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    report_service = ReportService(db)
    return report_service.update_report_by_id(
        selected_workspace_id,
        loggedin_user_id,
        report_id,
        field_name,
        field_value,
    )