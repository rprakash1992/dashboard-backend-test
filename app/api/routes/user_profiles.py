from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

# import core
from app.core.dashboard_database import get_dashboard_db
from app.core.dependencies import get_current_user_id

# import schemas
from app.schemas.user_profile import (
    UserProfileSchema,
    PutUserProfileSchema,
    PatchUserProfileSchema,
)

# import services
from app.services.user_profile import UserProfileService


router = APIRouter()


@router.get(
    "/{selected_workspace_id}/user-profiles", response_model=List[UserProfileSchema]
)
async def get_user_profile_by_user_ids_endpoint(
    selected_workspace_id: str,
    user_ids: List[str] = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not user_ids:
        raise HTTPException(status_code=400, detail="Invalid arguments.")
    else:
        service = UserProfileService(db)
        return service.get_user_profile_by_user_ids(
            selected_workspace_id, loggedin_user_id, user_ids
        )


@router.get(
    "/{selected_workspace_id}/user-profiles/search",
    response_model=List[UserProfileSchema],
)
async def search_user_profiles_endpoint(
    selected_workspace_id: str,
    search_text: str = Query(None),
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    if not (selected_workspace_id):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    service = UserProfileService(db)
    return service.search_user_profiles(
        selected_workspace_id, loggedin_user_id, search_text
    )


@router.get(
    "/{selected_workspace_id}/user-profiles/{user_id}", response_model=UserProfileSchema
)
async def get_user_profile_by_user_id_endpoint(
    selected_workspace_id: str,
    user_id: str,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    service = UserProfileService(db)

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid arguments.")
    elif user_id == "my-profile":

        return service.get_user_profile_by_user_id(
            selected_workspace_id, loggedin_user_id, loggedin_user_id
        )
    else:
        return service.get_user_profile_by_user_ids(
            selected_workspace_id, loggedin_user_id, [user_id]
        )[0]


@router.put(
    "/{selected_workspace_id}/user-profiles",
    response_model=UserProfileSchema,
)
async def update_user_profile_record(
    selected_workspace_id: str,
    body: PutUserProfileSchema,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):

    full_profile = body

    if not (selected_workspace_id and full_profile):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    service = UserProfileService(db)
    return service.update_full_user_profile(
        selected_workspace_id, loggedin_user_id, full_profile
    )


@router.patch(
    "/{selected_workspace_id}/user-profiles/{profile_id}",
    response_model=UserProfileSchema,
)
async def update_user_profiles_endpoint(
    selected_workspace_id: str,
    profile_id: str,
    body: PatchUserProfileSchema,
    db: Session = Depends(get_dashboard_db),
    loggedin_user_id: str = Depends(get_current_user_id),
):
    field_name = body.field_name
    field_value = body.field_value

    if not (selected_workspace_id and profile_id and field_name):
        raise HTTPException(status_code=400, detail="Invalid arguments.")

    service = UserProfileService(db)
    return await service.update_user_profile(
        selected_workspace_id,
        loggedin_user_id,
        profile_id,
        field_name,
        field_value,
    )
