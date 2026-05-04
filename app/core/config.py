from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

AWS_ACCESS_KEY = os.getenv("AWS_S3_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_S3_SECRET_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")

# resend api key
RESEND_ACCESS_KEY = os.getenv("RESEND_ACCESS_KEY")

# openai api key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# database
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# cors
CORS_ORIGINS = os.getenv("CORS_ORIGINS")
CORS_METHODS = os.getenv("CORS_METHODS")
CORS_HEADERS = os.getenv("CORS_HEADERS")

# Google OAuth
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

MODE = os.getenv("MODE")
ROOT_USER_EMAIL = [
    e.strip() for e in os.getenv("ROOT_USER_EMAIL", "").split(",") if e.strip()
]


class Settings(BaseSettings):
    # APP_NAME: str = "VCOLLAB.AI"
    APP_NAME: str = "VCollab Dashboard"
    APP_DOMAIN: str = "https://vcollab.ai"
    APP_EMAIL: str = "info@vcollab.ai"

    DEBUG: bool = False

    # Database
    DASHBOARD_DATABASE_URL: str = (
        os.getenv("DASHBOARD_DATABASE_URL")
        or f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLITE_DATABASE_URL: str = "sqlite:///./test.db"

    # CORS
    CORS_ORIGINS: list[str] = CORS_ORIGINS or ["*"]
    CORS_METHODS: list[str] = CORS_METHODS or ["*"]
    CORS_HEADERS: list[str] = CORS_HEADERS or ["*"]

    # AWS
    aws_access_key: str = AWS_ACCESS_KEY or ""
    aws_secret_key: str = AWS_SECRET_KEY or ""
    aws_region: str = AWS_REGION or ""
    aws_s3_bucket: str = AWS_S3_BUCKET or ""

    # Resend (Email)
    RESEND_API_KEY: str = RESEND_ACCESS_KEY or ""

    # OpenAI
    OPENAI_API_KEY: Optional[str] = OPENAI_API_KEY or ""

    # Workflow
    WORKFLOW_ROOT_FILE_NAME: str = "workflow.py"
    FLOW_FUNCTION_NAME: str = "workflow"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET: str = GOOGLE_CLIENT_SECRET
    FRONTEND_URL: str = FRONTEND_URL

    # deployment mode: local/production
    MODE: str = MODE or "production"

    # API route prefix — set to "/server" in production (ALB routes /server/* to backend)
    # Leave empty in local dev (Traefik strips the /server prefix before forwarding)
    API_PREFIX: str = (
        "/server/api/v1" if (MODE or "production") == "production" else "/api/v1"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
