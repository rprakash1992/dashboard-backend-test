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

    def insert_roles(self, new_roles: List[RoleSchema]) -> List[RoleSchema]:
        roles = [
            Role(
                id=new_role.id,
                item_type=new_role.item_type,
                scope=new_role.scope,
                field=new_role.field,
                can_create=new_role.can_create,
                can_read=new_role.can_read,
                can_update=new_role.can_update,
                can_delete=new_role.can_delete,
            )
            for new_role in new_roles
        ]
        self.db.add_all(roles)
        self.db.commit()
        for file in roles:
            self.db.refresh(file)
        return [RoleSchema.model_validate(f) for f in roles]
