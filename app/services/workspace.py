from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

# import repositories
from app.repositories.database_dashboard.relation import RelationRepository
from app.repositories.database_dashboard.item import ItemRepository

# import schemas
from app.schemas.item import ItemType, NewItemSchema, ItemSchema
from app.schemas.relation import RelationType

# import services
from app.services.role import RoleService
from app.services.relation import RelationSchema
from app.services.item import ItemService


class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db
        self.item_repo = ItemRepository(db)
        self.relation_repo = RelationRepository(db)
        self.item_service = ItemService(db)

    def insert_workspace(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
    ) -> ItemSchema:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_create_permission = role_service.has_create_item_permission(
            ItemType.PROJECT
        )

        if not has_create_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to create project."
            )

        new_item = NewItemSchema(
            title=title,
            item_type=ItemType.WORKSPACE,
            description=description,
            image=image,
            tags=tags,
        )
        insert_item_response = self.item_service.insert_item(
            selected_workspace_id, loggedin_user_id, new_item
        )
        return insert_item_response

    def fetch_my_workspaces(self, loggedin_user_id: str) -> List[ItemSchema]:
        all_workspace_items = self.item_repo.get_items_by_item_type(ItemType.WORKSPACE)

        all_workspace_items_ids = [item.id for item in all_workspace_items]

        relations = self.relation_repo.get_relations_by_source_ids_and_target_id(
            all_workspace_items_ids, loggedin_user_id
        )

        workspace_ids = [relation.source_id for relation in relations]

        items = self.item_repo.get_items_by_ids(workspace_ids)

        personal_ws_item = None
        admin_ws_item = None
        vcollab_we_item = None
        rest_ws_items = []

        for item in items:
            if item.system_key == "user_personal_workspace":
                item.title = "Me"
                personal_ws_item = item

            elif item.system_key == "system_administrator_workspace":
                admin_ws_item = item

            elif item.system_key == "vcollab_workspace":
                vcollab_we_item = item

            else:
                rest_ws_items.append(item)

        data = []

        if admin_ws_item and vcollab_we_item:
            data = [personal_ws_item] + [admin_ws_item] + [vcollab_we_item]

        elif vcollab_we_item and not admin_ws_item:
            data = [personal_ws_item] + [vcollab_we_item]

        elif admin_ws_item and not vcollab_we_item:
            data = [personal_ws_item] + [admin_ws_item]

        else:
            data = [personal_ws_item]

        if len(rest_ws_items) > 0:
            data = data + rest_ws_items

        return data

    def add_user_to_workspace(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        workspace_id: str,
        user_id_to_add: str,
        role_id_to_assign: str,
    ) -> ItemSchema:
        role_service = RoleService(workspace_id, loggedin_user_id, self.db)
        has_add_user_permission = role_service.has_add_user_to_workspace_permission()

        if not has_add_user_permission:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Ypu are not permitted to add users to this workspace.",
            )

        new_relation = RelationSchema(
            source_id=workspace_id,
            target_id=user_id_to_add,
            relation=f"role.{role_id_to_assign}",
        )

        self.relation_repo.insert_relations([new_relation])

        try:
            return self.item_repo.get_item_by_id(user_id_to_add)
        except IntegrityError:
            raise HTTPException(
                status_code=409, detail="User is already present in this workspace."
            )

    def add_item_to_workspace(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        workspace_id: str,
        item_id: str,
    ) -> bool:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_share_item_permission = (
            role_service.has_share_item_to_workspace_permission()
        )

        if not has_share_item_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to share items of this workspace.",
            )

        new_relation = RelationSchema(
            source_id=workspace_id,
            target_id=item_id,
            relation=RelationType.CHILD,
        )

        try:
            self.relation_repo.insert_relations([new_relation])
        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail="Item already exists in the workspace to which it is being shared.",
            )

        return True
    
    
    def fetch_workspace_users(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        workspace_id: str,
    ) -> List[ItemSchema]:
        role_service = RoleService(workspace_id, loggedin_user_id, self.db)
        has_read_items_permission = (
            role_service.has_read_items_permission()
        )

        if not has_read_items_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to read items of this workspace.",
            )
            
        relation_response = (
            self.relation_repo.get_relations_by_source_id_ilike_relation(
                workspace_id, "%role%"
            )
        )
        target_user_profile_ids = [
            relation.target_id for relation in relation_response
        ]
        return self.item_repo.get_items_by_ids(target_user_profile_ids)
