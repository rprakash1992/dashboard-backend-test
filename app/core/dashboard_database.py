from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine

from app.core.config import get_settings


# setting up postgres database session
settings = get_settings()
DASHBOARD_DATABASE_URL = settings.DASHBOARD_DATABASE_URL

engine_dashboard = create_engine(DASHBOARD_DATABASE_URL)
DashboardSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_dashboard)


class DashboardBase(DeclarativeBase):
    pass


def get_dashboard_db():
    db = DashboardSessionLocal()
    try:
        yield db
    finally:
        db.close()
