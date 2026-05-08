from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Any, Optional

# import repositories
from app.repositories.database_dashboard.role import RoleRepository
from app.repositories.database_dashboard.relation import RelationRepository
from app.repositories.database_dashboard.item import ItemRepository

# import schemas
# from app.schemas.role import RoleAction
from app.schemas.item import ItemType, NewItemSchema
from app.schemas.role import RoleSchema, NewRoleSchema, InsertRoleResponse


class RoleService:
    def __init__(self, workspace_id: str, user_id: str, db: Session):
        """
        Manages roles and permission of a user in a workspace.

        Args:
            workspace_id (str).
            user_id (str).
            db (Session): postgres database session.
        """
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.repo = RoleRepository(db)
        self.relations_repo = RelationRepository(db)
        self.item_repo = ItemRepository(db)

    def is_system_admin_user():
        pass

    def get_roles(self) -> List[RoleSchema]:
        """
        Gets the roles list based on what is the role of user in the workspace.

        Returns:
            Returns list of roles
        """
        relations = self.relations_repo.get_relations_by_source_id_and_target_id(
            self.workspace_id,
            self.user_id,
        )

        # Check if relations list is empty
        if not relations or len(relations) == 0:
            # means the loggedin user is not a user of selected workspace
            return []

        relation = relations[0]

        if not "role." in relation.relation:
            # if source_id is a workspace id and target_id is a user id, then the relation is saved as 'role.<some_role_id>' in the database.
            # So, the string "role." should be present in the relation
            return []

        # Remove first 05 characters from the relation to get the role_id
        role_id = relation.relation[5:]
        return self.repo.get_roles_by_id(role_id)

    def _find_role(
        self,
        roles: Any,
        item_type: ItemType,
        scope: str,
        field: str,
        operation: str,
    ):
        return next(
            (
                role
                for role in roles
                if role.item_type == item_type
                and role.scope == scope
                and role.field == field
                and getattr(role, operation, None) == True
            ),
            None,
        )

    def has_create_title_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "title", "can_create"
        )
        return True if role_found else False

    def has_read_title_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(_roles, item_type, "metadata", "title", "can_read")
        return True if role_found else False

    def has_update_title_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "title", "can_update"
        )
        return True if role_found else False

    def has_delete_title_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "title", "can_delete"
        )
        return True if role_found else False

    def has_create_description_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "description", "can_create"
        )
        return True if role_found else False

    def has_read_description_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "description", "can_read"
        )
        return True if role_found else False

    def has_update_description_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "description", "can_update"
        )
        return True if role_found else False

    def has_delete_description_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "description", "can_delete"
        )
        return True if role_found else False

    def has_create_image_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "image", "can_create"
        )
        return True if role_found else False

    def has_read_image_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(_roles, item_type, "metadata", "image", "can_read")
        return True if role_found else False

    def has_update_image_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "image", "can_update"
        )
        return True if role_found else False

    def has_delete_image_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "image", "can_delete"
        )
        return True if role_found else False

    def has_create_tags_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "tags", "can_create"
        )
        return True if role_found else False

    def has_read_tags_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(_roles, item_type, "metadata", "tags", "can_read")
        return True if role_found else False

    def has_update_tags_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "tags", "can_update"
        )
        return True if role_found else False

    def has_delete_tags_permission(
        self, item_type: ItemType, roles: Optional[Any] = None
    ) -> bool:
        _roles = roles or self.get_roles()
        role_found = self._find_role(
            _roles, item_type, "metadata", "tags", "can_delete"
        )
        return True if role_found else False

    def has_create_item_permission(self, item_type: ItemType) -> bool:
        roles = self.get_roles()

        title_permission = self.has_create_title_permission(item_type, roles)
        description_permission = self.has_create_description_permission(
            item_type, roles
        )
        image_permission = self.has_create_image_permission(item_type, roles)
        tags_permission = self.has_create_tags_permission(item_type, roles)
        has_create_item_permission = (
            title_permission
            and description_permission
            and image_permission
            and tags_permission
        )
        return has_create_item_permission

    def has_read_items_permission(self, item_type: ItemType) -> bool:
        roles = self.get_roles()

        title_permission = self.has_read_title_permission(item_type, roles)
        description_permission = self.has_read_description_permission(item_type, roles)
        image_permission = self.has_read_image_permission(item_type, roles)
        tags_permission = self.has_read_tags_permission(item_type, roles)
        has_read_item_permission = (
            title_permission
            and description_permission
            and image_permission
            and tags_permission
        )
        return has_read_item_permission

    def has_read_file_items_permission(self) -> bool:
        return self.has_read_items_permission(ItemType.FILE)

    def has_read_project_items_permission(self) -> bool:
        return self.has_read_items_permission(ItemType.FILE)

    def has_read_report_items_permission(self) -> bool:
        return self.has_read_items_permission(ItemType.FILE)

    def has_read_workspace_items_permission(self) -> bool:
        return self.has_read_items_permission(ItemType.FILE)

    def has_read_user_profile_items_permission(self) -> bool:
        return self.has_read_items_permission(ItemType.FILE)

    def has_read_job_items_permission(self) -> bool:
        return self.has_read_items_permission(ItemType.FILE)

    def has_read_workflow_items_permission(self) -> bool:
        return self.has_read_items_permission(ItemType.FILE)

    def has_read_all_items_permission(self) -> bool:
        permission = (
            self.has_read_file_items_permission
            and self.has_read_project_items_permission
            and self.has_read_report_items_permission
            and self.has_read_workspace_items_permission
            and self.has_read_user_profile_items_permission
            and self.has_read_job_items_permission
            and self.has_read_workflow_items_permission
        )
        return permission

    def has_update_item_permission(self, item_type: ItemType) -> bool:
        roles = self.get_roles()

        title_permission = self.has_update_title_permission(item_type, roles)
        description_permission = self.has_update_description_permission(
            item_type, roles
        )
        image_permission = self.has_update_image_permission(item_type, roles)
        tags_permission = self.has_update_tags_permission(item_type, roles)
        has_update_item_permission = (
            title_permission
            and description_permission
            and image_permission
            and tags_permission
        )
        return has_update_item_permission

    def has_update_item_field_permission(self, item_type: ItemType, field: str) -> bool:
        if field == "title":
            return self.has_update_title_permission(item_type)
        if field == "description":
            return self.has_update_description_permission(item_type)
        if field == "image":
            return self.has_update_image_permission(item_type)
        if field == "tags":
            return self.has_update_tags_permission(item_type)
        return False

    def has_delete_item_permission(self, item_type: ItemType) -> bool:
        roles = self.get_roles()

        title_permission = self.has_delete_title_permission(item_type, roles)
        description_permission = self.has_delete_description_permission(
            item_type, roles
        )
        image_permission = self.has_delete_image_permission(item_type, roles)
        tags_permission = self.has_delete_tags_permission(item_type, roles)
        has_delete_item_permission = (
            title_permission
            and description_permission
            and image_permission
            and tags_permission
        )
        return has_delete_item_permission

    def has_create_content_permission(
        self, item_type: ItemType, field: Optional[str] = None
    ) -> bool:
        roles = self.get_roles()
        role_found = self._find_role(
            roles, item_type, "content", field or "all", "can_create"
        )
        return True if role_found else False

    def has_read_content_permission(
        self, item_type: ItemType, field: Optional[str] = None
    ) -> bool:
        roles = self.get_roles()
        role_found = self._find_role(
            roles, item_type, "content", field or "all", "can_read"
        )
        return True if role_found else False

    def has_update_content_permission(
        self, item_type: ItemType, field: Optional[str] = None
    ) -> bool:
        roles = self.get_roles()
        role_found = self._find_role(
            roles, item_type, "content", field or "all", "can_update"
        )
        return True if role_found else False

    def has_delete_content_permission(
        self, item_type: ItemType, field: Optional[str] = None
    ) -> bool:
        roles = self.get_roles()
        role_found = self._find_role(
            roles, item_type, "content", field or "all", "can_delete"
        )
        return True if role_found else False

    def insert_role(
        self,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        permissions: List[NewRoleSchema],
    ) -> InsertRoleResponse:
        has_create_item_permission = self.has_create_item_permission(ItemType.ROLE)
        has_create_content_permission = self.has_create_content_permission(
            ItemType.ROLE
        )

        has_create_role_permission = (
            has_create_item_permission and has_create_content_permission
        )

        if not has_create_role_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have the permission to create role in this workspace.",
            )

        item = NewItemSchema(
            title=title,
            item_type=ItemType.ROLE,
            description=description,
            image=image,
            tags=tags,
        )
        new_item_response = self.item_repo.insert_items([item])
        new_item = new_item_response[0]
        new_item_id = new_item.id

        new_roles = []
        for permission in permissions:
            new_role = RoleSchema(
                id=new_item_id,
                item_type=permission.item_type,
                scope=permission.scope,
                field=permission.field,
                can_create=permission.can_create,
                can_read=permission.can_read,
                can_update=permission.can_update,
                can_delete=permission.can_delete,
            )
            new_roles.append(new_role)

        role = self.repo.insert_roles(new_roles)
        return InsertRoleResponse(item=new_item, role=role)
