from sqlalchemy.orm import Session
from typing import List
from app.repositories.database_dashboard.base import BaseRepository
from app.models.role import Role
from app.schemas.role import RoleSchema


class RoleRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_roles_by_id(self, role_id: str) -> List[RoleSchema]:
        roles = (
            self.db.query(Role)
            .filter(
                Role.id == role_id,
            )
            .all()
        )
        return [RoleSchema.model_validate(f) for f in roles]
