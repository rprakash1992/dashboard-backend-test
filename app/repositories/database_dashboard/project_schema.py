from sqlalchemy.orm import Session
from typing import List
from app.repositories.database_dashboard.base import BaseRepository
from app.models.project_schema import ProjectSchema
from app.schemas.project_schema import ProjectSchemaSchema


class ProjectSchemaRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_all_project_schemas(self) -> List[ProjectSchemaSchema]:
        project_schemas = self.db.query(ProjectSchema).all()
        return [ProjectSchemaSchema.model_validate(f) for f in project_schemas]
