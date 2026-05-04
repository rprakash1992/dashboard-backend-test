from sqlalchemy.orm import Session
from typing import List

# import models
from app.models.project import Project

# import repositories
from app.repositories.database_dashboard.base import BaseRepository

# import schemas
from app.schemas.project import ProjectSchema


class ProjectRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_projects_by_ids(self, ids: List[str]) -> List[ProjectSchema]:
        projects = (
            self.db.query(Project)
            .filter(
                Project.project.in_(ids),
            )
            .all()
        )
        return [ProjectSchema.model_validate(f) for f in projects]

    def insert_projects(self, new_projects: List[ProjectSchema]) -> List[ProjectSchema]:
        projects = [
            Project(
                project=new_project.project,
                file=new_project.file,
                file_parameters=new_project.file_parameters,
            )
            for new_project in new_projects
        ]
        self.db.add_all(projects)
        self.db.commit()
        for project in projects:
            self.db.refresh(project)
        return [ProjectSchema.model_validate(f) for f in projects]
