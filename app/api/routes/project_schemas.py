from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.project_schema import ProjectSchemaSchema

# import services
from app.services.project_schema import ProjectSchemaService


router = APIRouter()


@router.get("/project-schemas", response_model=List[ProjectSchemaSchema])
async def get_project_schemas_endpoint(
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    service = ProjectSchemaService(db)
    return service.fetch_project_schemas()
