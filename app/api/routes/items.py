from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
import json

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.item import ItemSchema, UpdateItemSchema

# import services
from app.services.item import ItemService


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


@router.get("/{selected_workspace_id}/items", response_model=List[ItemSchema])
async def get_item_by_ids_endpoint(
    selected_workspace_id: str,
    item_ids: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    item_ids = json.loads(item_ids)

    if not (selected_workspace_id and item_ids and len(item_ids) > 0):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    item_service = ItemService(db)
    return item_service.fetch_items_by_ids(
        selected_workspace_id,
        loggedin_user_id,
        item_ids,
    )


@router.get(
    "/{selected_workspace_id}/items/{item_type}/search",
    response_model=List[ItemSchema],
)
async def search_items(
    selected_workspace_id: str,
    item_type: str,
    search_text: str = Query(""),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (item_type and selected_workspace_id and search_text):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    item_service = ItemService(db)
    return item_service.search_items(
        selected_workspace_id,
        loggedin_user_id,
        item_type,
        search_text,
    )


@router.get("/{selected_workspace_id}/items/{item_id}/traceability")
async def get_item_traceability_endpoint(
    selected_workspace_id: str,
    item_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (item_id and selected_workspace_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    item_service = ItemService(db)
    return item_service.fetch_item_traceability(
        selected_workspace_id, loggedin_user_id, item_id
    )


@router.get(
    "/{selected_workspace_id}/items/{selected_item_type}",
    response_model=List[ItemSchema],
)
async def get_dashboard_items_endpoint(
    selected_workspace_id: str,
    selected_item_type: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (selected_item_type and selected_workspace_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    item_service = ItemService(db)
    return item_service.fetch_dashboard_items(
        selected_workspace_id,
        loggedin_user_id,
        selected_item_type,
    )


@router.patch(
    "/{selected_workspace_id}/items/{selected_item_type}/{item_id}",
    response_model=ItemSchema,
)
async def update_item_metadata(
    selected_workspace_id: str,
    selected_item_type: str,
    item_id: str,
    body: UpdateItemSchema,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    field_name = body.field_name
    field_value = body.field_value

    if not (selected_workspace_id and item_id and selected_item_type and field_name):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    item_service = ItemService(db)
    return item_service.update_item_metadata(
        selected_workspace_id,
        loggedin_user_id,
        item_id,
        selected_item_type,
        field_name,
        field_value,
    )


@router.delete(
    "/{selected_workspace_id}/items/{selected_item_type}/{item_id}",
    response_model=ItemSchema,
)
async def delete_item_endpoint(
    selected_workspace_id: str,
    selected_item_type: str,
    item_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (selected_workspace_id and item_id and selected_item_type):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    item_service = ItemService(db)
    return item_service.delete_item(
        selected_workspace_id,
        loggedin_user_id,
        item_id,
        selected_item_type,
    )


# @router.get("/items/workspaces", response_model=List[ItemSchema])
# async def get_root_workspaces_endpoint(
#     db: Session = Depends(get_dashboard_db),
#     loggedin_user_id: str = Depends(get_current_user_id),
# ):
#     item_service = ItemService(db)
#     return item_service.get_my_workspaces(loggedin_user_id)
