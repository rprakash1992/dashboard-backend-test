from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.view import ViewSchema, PatchViewSchema, CreateViewSchema

# import services
from app.services.view import ViewService


router = APIRouter()


@router.get("/views", response_model=List[ViewSchema])
async def get_dashboard_views_endpoint(
    item_type: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    service = ViewService(db)
    return service.fetch_dashboard_views(loggedin_user_id, item_type)


@router.post("/views", response_model=List[ViewSchema])
async def insert_view_endpoint(
    body: CreateViewSchema,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not body:
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    service = ViewService(db)
    return service.insert_view(loggedin_user_id, body)


@router.put("/views/{view_id}", response_model=ViewSchema)
async def update_full_view(
    view_id: str,
    body: ViewSchema,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not body:
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    service = ViewService(db)
    return service.update_full_view(loggedin_user_id, view_id, body)


@router.patch("/views/{view_id}", response_model=ViewSchema)
async def update_view_by_id(
    view_id: str,
    body: PatchViewSchema,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    field_name = body.field_name
    field_value = body.field_value

    if not field_name:
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    service = ViewService(db)
    return service.update_view_by_id(loggedin_user_id, view_id, field_name, field_value)


@router.delete("/views/{view_id}")
async def delete_view_by_id_endpoint(
    view_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not view_id:
        raise HTTPException(status_code=400, detail="View Id not found in the request.")

    service = ViewService(db)
    return service.delete_view_by_id(loggedin_user_id, view_id)
