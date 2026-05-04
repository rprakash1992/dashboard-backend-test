from sqlalchemy.orm import Session
from typing import List

# import repositories
from app.repositories.database_dashboard.project_schema import ProjectSchemaRepository

# import schemas
from app.schemas.project_schema import ProjectSchemaSchema


class ProjectSchemaService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectSchemaRepository(db)

    def fetch_project_schemas(self) -> List[ProjectSchemaSchema]:
        return self.repo.get_all_project_schemas()
