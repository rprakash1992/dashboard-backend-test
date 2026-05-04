from fastapi import APIRouter
from app.api.routes import (
    views,
    files,
    projects,
    reports,
    file_upload,
    tags,
    items,
    jobs,
    project_schemas,
    workflows,
    workspaces,
    user_profiles,
    chat,
    auth,
    roles,
)

api_router = APIRouter()

api_router.include_router(views.router, tags=["Views"])
api_router.include_router(files.router, tags=["Files"])
api_router.include_router(projects.router, tags=["Projects"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(tags.router, tags=["Tags"])
api_router.include_router(items.router, tags=["Items"])
api_router.include_router(jobs.router, tags=["Jobs"])
api_router.include_router(project_schemas.router, tags=["Project-Schemas"])
api_router.include_router(workflows.router, tags=["Workflows"])
api_router.include_router(workspaces.router, tags=["Workspaces"])
api_router.include_router(user_profiles.router, tags=["User-Profiles"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(file_upload.router, tags=["File-Upload"])
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(roles.router, tags=["Roles"])
