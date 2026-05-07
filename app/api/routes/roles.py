from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import repositories
from app.repositories.database_dashboard.role import RoleRepository

# import schemas
from app.schemas.item import ItemType
from app.schemas.role import InsertRoleResponse, RoleSchema, NewRoleSchema

# import services
from app.services.role import RoleService

router = APIRouter()


class InsertRoleRequest(BaseModel):
    permissions: List[NewRoleSchema]
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None


@router.post(
    "/{selected_workspace_id}/roles",
    response_model=InsertRoleResponse,
)
async def insert_role(
    selected_workspace_id: str,
    body: InsertRoleRequest,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    permissions = body.permissions
    title = body.title
    description = body.description or ""
    image = body.image or ""
    tags = body.tags or []

    if not (title and selected_workspace_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    role_service = RoleService(selected_workspace_id, loggedin_user_id, db)
    return role_service.insert_role(
        title,
        description,
        image,
        tags,
        permissions,
    )


@router.get(
    "/{selected_workspace_id}/roles/{role_id}/permissions",
    response_model=List[RoleSchema],
)
async def get_role_permissions(
    selected_workspace_id: str,
    role_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (role_id and selected_workspace_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    role_service = RoleService(selected_workspace_id, loggedin_user_id, db)
    has_read_content_permission = role_service.has_read_content_permission(
        ItemType.ROLE
    )

    if not has_read_content_permission:
        raise HTTPException(
            status_code=403,
            detail="You don't have the permission to read role content in this workspace.",
        )

    role_repo = RoleRepository(db)
    return role_repo.get_roles_by_id(role_id)
