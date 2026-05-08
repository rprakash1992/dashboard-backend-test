from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.item import ItemSchema, WorkspaceUserSchema

# import services
from app.services.workspace import WorkspaceService

router = APIRouter()


class InsertWorkspaceRequest(BaseModel):
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None


class AddUserRequest(BaseModel):
    user_id: str
    role_id: str
    workspace_id: str


class AddItemRequest(BaseModel):
    workspace_id: str
    item_id: str


class WorkspaceUsersRequest(BaseModel):
    workspace_id: str


@router.get("/workspaces/my", response_model=List[ItemSchema])
async def fetch_my_workspaces(
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    workspace_service = WorkspaceService(db)
    return workspace_service.fetch_my_workspaces(loggedin_user_id)


# @router.post("/{selected_workspace_id}/workspaces/users", response_model=List[ItemSchema])
@router.post(
    "/{selected_workspace_id}/workspaces/users",
    response_model=List[WorkspaceUserSchema],
)
async def fetch_workspace_users(
    selected_workspace_id: str,
    body: WorkspaceUsersRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    workspace_id = body.workspace_id
    print(workspace_id, selected_workspace_id)
    if not (selected_workspace_id and workspace_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    workspace_service = WorkspaceService(db)
    return workspace_service.fetch_workspace_users(
        selected_workspace_id, loggedin_user_id, workspace_id
    )


@router.post("/{selected_workspace_id}/workspaces", response_model=ItemSchema)
async def insert_workspace(
    selected_workspace_id: str,
    body: InsertWorkspaceRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    title = body.title
    description = body.description or ""
    image = body.image or ""
    tags = body.tags or []

    if not (selected_workspace_id and title):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    workspace_service = WorkspaceService(db)
    return workspace_service.insert_workspace(
        selected_workspace_id, loggedin_user_id, title, description, image, tags
    )


# @router.post("/{selected_workspace_id}/workspaces/new-user", response_model=ItemSchema)
@router.post(
    "/{selected_workspace_id}/workspaces/new-user", response_model=WorkspaceUserSchema
)
async def add_user_to_workspace(
    selected_workspace_id: str,
    body: AddUserRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    user_id = body.user_id
    role_id = body.role_id
    workspace_id = body.workspace_id

    if not (selected_workspace_id and user_id and role_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    workspace_service = WorkspaceService(db)
    return workspace_service.add_user_to_workspace(
        selected_workspace_id, loggedin_user_id, workspace_id, user_id, role_id
    )


# @router.post("/{selected_workspace_id}/workspaces/update-user", response_model=ItemSchema)
@router.post(
    "/{selected_workspace_id}/workspaces/update-user",
    response_model=WorkspaceUserSchema,
)
async def update_workspac_user_role(
    selected_workspace_id: str,
    body: AddUserRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    user_id = body.user_id
    role_id = body.role_id
    workspace_id = body.workspace_id

    if not (selected_workspace_id and user_id and role_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    workspace_service = WorkspaceService(db)
    return workspace_service.update_workspace_user_role(
        selected_workspace_id, loggedin_user_id, workspace_id, user_id, role_id
    )


@router.post("/{selected_workspace_id}/workspaces/new-item", response_model=bool)
async def add_item_to_workspace(
    selected_workspace_id: str,
    body: AddItemRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    workspace_id = body.workspace_id
    item_id = body.item_id

    if not (selected_workspace_id and item_id and workspace_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    workspace_service = WorkspaceService(db)
    return workspace_service.add_item_to_workspace(
        selected_workspace_id, loggedin_user_id, workspace_id, item_id
    )
