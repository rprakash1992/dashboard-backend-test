from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Any

# import repositories
from app.repositories.database_dashboard.item_activity import ItemActivityRepository

# import services
from app.services.role import RoleService

# import services
from app.schemas.item_activity import ItemActivitySchema
from app.schemas.item import ItemType, ItemSchema

# import utils
from app.utils.misc import (
    get_current_time,
)


class ItemActivityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ItemActivityRepository(db)

    async def get_item_activities_by_id(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
        item_type: ItemType,
    ) -> List[ItemActivitySchema]:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_metadata_permission = role_service.has_create_item_permission(
            item_type
        )

        if not has_read_metadata_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to read item."
            )

        return self.repo.get_item_activities_by_id(item_id)

    def create_new_item_activity(
        self, user_id: str, item_id: str, item_title: str, item_type: ItemType
    ) -> ItemActivitySchema:
        content_text = f"Created new {item_type}: '{item_title}'."

        new_item_activity = ItemActivitySchema(
            user_id=user_id,
            item_id=item_id,
            prev_action=None,
            timestamp=get_current_time(),
            activity_type="activity",
            content=content_text,
        )
        activities = self.repo.insert_item_activities([new_item_activity])
        return activities[0]

    def create_edit_item_activity(
        self,
        user_id: str,
        old_item: ItemSchema,
        updated_field_name: str,
        updated_field_value: Any,
    ) -> ItemActivitySchema:
        content_text = ""
        item_id = old_item.id

        if updated_field_name == "image":
            content_text = f"Updated image."
        elif updated_field_name == "tags":
            old_tags = old_item.tags
            new_tags = updated_field_value if updated_field_value else []

            if len(old_tags) < len(new_tags):
                added_tags = [tag for tag in new_tags if tag not in old_tags]
                content_text = f"Added tag: '{added_tags[0]}'."
            elif len(old_tags) > len(new_tags):
                removed_tags = [tag for tag in old_tags if tag not in new_tags]
                content_text = f"Removed tag: '{removed_tags[0]}'."
        else:
            content_text = f"Updated {updated_field_name} to '{updated_field_value}'."

        new_item_activity = ItemActivitySchema(
            user_id=user_id,
            item_id=item_id,
            prev_action=None,
            timestamp=get_current_time(),
            activity_type="activity",
            content=content_text,
        )
        activities = self.repo.insert_item_activities([new_item_activity])
        return activities[0]

    def create_download_activity(
        self, loggedin_user_id: str, item_id: str, item_type: str
    ) -> ItemActivitySchema:
        content_text = f"Downloaded {item_type}."

        new_item_activity = ItemActivitySchema(
            user_id=loggedin_user_id,
            item_id=item_id,
            prev_action=None,
            timestamp=get_current_time(),
            activity_type="activity",
            content=content_text,
        )
        activities = self.repo.insert_item_activities([new_item_activity])
        return activities[0]
