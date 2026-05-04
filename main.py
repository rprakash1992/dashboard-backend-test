from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
# load all environment variables
load_dotenv()

from app.core.sqlite_database import SqliteBase, engine_sqlite
from app.core.dashboard_database import DashboardBase, engine_dashboard
from app.core.config import get_settings
from app.middlewares.user_info import UserInfoMiddleware

from app.api.router import api_router
from app.models import (
    file,
    item_activities,
    item,
    job,
    project_schema,
    project,
    relation,
    report,
    role,
    tag,
    user_profile,
    view,
    workflow,
)  # noqa: F401 - ensures models are registered with Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI starting up...")
    DashboardBase.metadata.create_all(bind=engine_dashboard)
    SqliteBase.metadata.create_all(bind=engine_sqlite)

    yield
    print("FastAPI shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(UserInfoMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    print(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
