from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.tag import TagSchema, CreateTagSchema

# import services
from app.services.tag import TagService


router = APIRouter()


@router.get("/tags", response_model=List[TagSchema])
async def get_all_tags_endpoint(
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    tag_service = TagService(db)
    return tag_service.fetch_all_tags()


@router.post("/tags", response_model=List[TagSchema])
async def insert_tags_endpoint(
    body: List[CreateTagSchema],
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    new_tags = body

    tag_service = TagService(db)
    return tag_service.insert_tags(new_tags)
