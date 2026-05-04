from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id
from app.schemas.role import RoleSchema
from app.repositories.database_dashboard.role import RoleRepository


router = APIRouter()


@router.get("/roles/{role_id}/permissions", response_model=List[RoleSchema])
async def get_role_permissions(
    role_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not role_id:
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    role_repo = RoleRepository(db)
    return role_repo.get_roles_by_id(role_id)
