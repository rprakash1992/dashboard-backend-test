from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine

from app.core.config import get_settings


# setting up sqlite database session
settings = get_settings()
engine_sqlite = create_engine(settings.SQLITE_DATABASE_URL)
SqliteSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_sqlite)


class SqliteBase(DeclarativeBase):
    pass


def get_sqlite_db():
    db = SqliteSessionLocal()
    try:
        yield db
    finally:
        db.close()
