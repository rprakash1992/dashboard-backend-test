from sqlalchemy.orm import Session
from typing import List
from app.repositories.database_dashboard.base import BaseRepository
from app.models.item_activities import ItemActivity
from app.schemas.item_activity import ItemActivitySchema


class ItemActivityRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_item_activities_by_id(self, item_id: str) -> List[ItemActivitySchema]:
        activities = (
            self.db.query(ItemActivity)
            .filter(
                ItemActivity.item_id == item_id,
            )
            .all()
        )
        return [ItemActivitySchema.model_validate(f) for f in activities]

    def insert_item_activities(
        self, new_activities: List[ItemActivitySchema]
    ) -> List[ItemActivitySchema]:
        activities = [
            ItemActivity(
                user_id=new_activity.user_id,
                item_id=new_activity.item_id,
                prev_action=new_activity.prev_action,
                timestamp=new_activity.timestamp,
                activity_type=new_activity.activity_type,
                content=new_activity.content,
            )
            for new_activity in new_activities
        ]

        self.db.add_all(activities)
        self.db.commit()
        for activity in activities:
            self.db.refresh(activity)
        return [ItemActivitySchema.model_validate(f) for f in activities]
