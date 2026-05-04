from sqlalchemy.orm import Session
from typing import List

# import repositories
from app.repositories.database_dashboard.role import RoleRepository
from app.repositories.database_dashboard.relation import RelationRepository
from app.repositories.database_dashboard.item import ItemRepository

# import schemas
from app.schemas.role import RoleAction
from app.schemas.item import ItemType
from app.schemas.role import RoleSchema


class RoleService:
    def __init__(self, selected_workspace_id: str, loggedin_user_id: str, db: Session):
        """
        Manages roles and permission of a user in a workspace.

        Args:
            workspace_id (str).
            user_id (str).
            db (Session): postgres database session.
        """
        self.workspace_id = selected_workspace_id
        self.user_id = loggedin_user_id
        self.repo = RoleRepository(db)
        self.relations_repo = RelationRepository(db)
        self.item_repo = ItemRepository(db)

    def is_system_admin_user():
        pass

    def get_roles(self) -> List[RoleSchema]:
        """
        Gets the roles list based on what is the role of loggedin user in the selected workspace.

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

    def has_read_items_permission(self) -> bool:
        """
        Checks if a user has the permission to read items in a workspace.

        A user will have permission to read metadata of an item in a workspace if there a role exists for which
        item_type is "workspace" and action is "read_items".

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        role_found = next(
            (
                role
                for role in roles
                if role.item_type == ItemType.WORKSPACE
                and role.action == RoleAction.READ_ITEMS
            ),
            None,
        )

        return True if role_found else False

    def has_read_metadata_permission(self, item_type: ItemType) -> bool:
        """
        Checks if a user has the permission to read metadata of an item in a workspace.

        A user will have permission to read metadata of an item in a workspace if there a role exists for which
        item_type is {item_type} provided in the argument and action is "read_metadata".

        Args:
            item_type: ItemType enum

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        role_found = next(
            (
                role
                for role in roles
                if role.item_type == item_type
                and role.action == RoleAction.READ_METADATA
            ),
            None,
        )

        return True if role_found else False

    def has_read_content_permission(self, item_type: ItemType) -> bool:
        """
        Checks if a user has the permission to read contents of an item in a workspace.
        Here, content refers to the table corresponding to the item_type. For e.g "files" table for item_type = "file"

        A user will have permission to read contents of an item in a workspace if there a role exists for which
        item_type is {item_type} provided in the argument and action is "read_contents".

        Args:
            item_type: ItemType enum

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        role_found = next(
            (
                role
                for role in roles
                if role.item_type == item_type
                and role.action == RoleAction.READ_CONTENTS
                and role.sections == ["*"]
            ),
            None,
        )

        return True if role_found else False

    def has_update_content_permission(self, item_type: ItemType) -> bool:
        """
        Checks if a user has the permission to update contents of an item in a workspace.
        Here, content refers to the table corresponding to the item_type. For e.g "files" table for item_type = "file"

        A user will have permission to update content of an item in a workspace if there a role exists for which
        item_type is {item_type} provided in the argument and action is "update_contents".

        Args:
            item_type: ItemType enum

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        role_found = next(
            (
                role
                for role in roles
                if role.item_type == item_type
                and role.action == RoleAction.UPDATE_CONTENTS
                and role.sections == ["*"]
            ),
            None,
        )

        return True if role_found else False

    def has_edit_full_metadata_permission(self, item_type: ItemType) -> bool:
        """
        Checks if a user has the permission to edit all metadata fields of an item in a workspace.

        A user will have permission to edit all metadata fields of an item in a workspace if there a role exists for which
        item_type is {item_type} provided in the argument, action is "update_metadata" and sections either contains all the metadata fields
        such as "title", "description", "image", "tags" or sections = ["*"].

        Args:
            item_type: Can be either ItemType enum or string value

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        has_permission = False

        for role in roles:
            role_item_type = role.item_type
            role_action = role.action
            role_sections = role.sections
            has_all_sections_permission = (
                ("title" in role_sections)
                and ("description" in role_sections)
                and ("image" in role_sections)
                and ("tags" in role_sections)
            ) or role_sections == ["*"]
            has_permission = (
                role_item_type == item_type
                and role_action == RoleAction.UPDATE_METADATA
                and has_all_sections_permission
            )
            if has_permission:
                break

        return has_permission

    def has_edit_metadata_permission(
        self, item_type: ItemType, item_metadata_field_name: str
    ) -> bool:
        """
        Checks if a user has the permission to edit a metadata field of an item in a workspace.

        A user will have permission to edit a metadata field of an item in a workspace if there is a role exists for which
        item_type is {item_type} provided in the argument, action is "update_metadata" and sections contains the {item_metadata_field_name} provided in the argument.

        Args:
            item_type: Can be either ItemType enum or string value

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        role_found = next(
            (
                role
                for role in roles
                if role.item_type == item_type
                and role.action == RoleAction.UPDATE_METADATA
                and item_metadata_field_name in role.sections
            ),
            None,
        )

        return True if role_found else False

    def has_delete_item_permission(self, item_type: ItemType) -> bool:
        """
        Checks if a user has the permission to delete an item in a workspace.

        A user will have permission to delete an item in a workspace if there is a role exists for which
        item_type is {item_type} provided in the argument and action is "delete".

        Args:
            item_type: ItemType enum

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        role_found = next(
            (
                role
                for role in roles
                if role.item_type == item_type and role.action == RoleAction.DELETE
            ),
            None,
        )

        return True if role_found else False

    def has_create_item_permission(self, item_type: ItemType) -> bool:
        """
        Checks if a user has the permission to create a new item in a workspace.

        A user will have permission to create a new item in a workspace if there a role exists for which
        item_type is {item_type} provided in the argument and action is "create".

        Args:
            item_type: ItemType enum

        Returns:
            True id user has the required permission, else False
        """
        roles = self.get_roles()

        role_found = next(
            (
                role
                for role in roles
                if role.item_type == item_type and role.action == RoleAction.CREATE
            ),
            None,
        )

        return True if role_found else False

    def has_share_item_to_workspace_permission(self):
        is_system_admin_role = self.is_system_administrator_role()
        is_admin_role = self.is_admin_role()
        is_private_user_role = self.is_private_user_role()

        return is_system_admin_role or is_admin_role or is_private_user_role

    def has_add_user_to_workspace_permission(self):
        is_system_admin_role = self.is_system_administrator_role()
        is_admin_role = self.is_admin_role()

        return is_system_admin_role or is_admin_role

    def has_update_profile_status_permission(self):
        return self.is_system_administrator_role()

    def is_private_user_role(self) -> bool:
        relations_resp = self.relations_repo.get_relations_by_source_id_and_target_id(
            self.workspace_id, self.user_id
        )

        if len(relations_resp) <= 0:
            return False

        relation = relations_resp[0].relation

        if not "role." in relation:
            # if source_id is a workspace id and target_id is a user id, then the relation is saved as 'role.<some_role_id>' in the database.
            # So, the string "role." should be present in the relation
            return False

        # Remove first 05 characters from the relation to get the role_id
        role_id = relation[5:]

        item = self.item_repo.get_item_by_id(role_id)

        if not item:
            return False

        system_key = item.system_key

        if system_key != "private_user_role":
            return False

        return True

    def is_admin_role(self) -> bool:
        # return self.user_id == "dd58b077-bbc2-4dbf-97a6-5f8be5d23c98"
        relations_resp = self.relations_repo.get_relations_by_source_id_and_target_id(
            self.workspace_id, self.user_id
        )

        if len(relations_resp) <= 0:
            return False

        relation = relations_resp[0].relation

        if not "role." in relation:
            # if source_id is a workspace id and target_id is a user id, then the relation is saved as 'role.<some_role_id>' in the database.
            # So, the string "role." should be present in the relation
            return []

        # Remove first 05 characters from the relation to get the role_id
        role_id = relation[5:]

        item = self.item_repo.get_item_by_id(role_id)

        if not item:
            return False

        system_key = item.system_key

        if system_key != "workspace_admin_role":
            return False

        return True

    def is_system_administrator_role(self) -> bool:
        # return self.user_id == "260f0217-32ab-4a07-a428-0f9cfdfe20b3"
        relations_resp = self.relations_repo.get_relations_by_source_id_and_target_id(
            self.workspace_id, self.user_id
        )

        if len(relations_resp) <= 0:
            return False

        relation = relations_resp[0].relation

        if not "role." in relation:
            # if source_id is a workspace id and target_id is a user id, then the relation is saved as 'role.<some_role_id>' in the database.
            # So, the string "role." should be present in the relation
            return False

        # Remove first 05 characters from the relation to get the role_id
        role_id = relation[5:]

        item = self.item_repo.get_item_by_id(role_id)

        if not item:
            return False

        system_key = item.system_key

        if system_key != "system_administrator_role":
            return False

        return True
