from typing import List
from sqlalchemy.orm import Session
from app.schemas.view import ViewSchema, CreateViewSchema
from app.models.view import View
from app.repositories.database_dashboard.base import BaseRepository


class ViewRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_views_by_owner(self, owner: str) -> List[ViewSchema]:
        views = self.db.query(View).filter(View.owner == owner).all()
        return [ViewSchema.model_validate(f) for f in views]

    def get_views_by_null_owner(self) -> List[ViewSchema]:
        views = self.db.query(View).filter(View.owner == None).all()
        return [ViewSchema.model_validate(f) for f in views]

    def get_views_by_id_and_owner(self, view_id: str, owner: str) -> List[ViewSchema]:
        views = (
            self.db.query(View).filter(View.id == view_id, View.owner == owner).all()
        )
        return [ViewSchema.model_validate(f) for f in views]

    def get_views_by_item_type_and_owner(
        self, item_type: str, owner: str
    ) -> List[ViewSchema]:
        views = (
            self.db.query(View)
            .filter(View.item_type == item_type, View.owner == owner)
            .all()
        )
        return [ViewSchema.model_validate(f) for f in views]

    def get_views_by_item_type_and_null_owner(self, item_type: str) -> List[ViewSchema]:
        views = (
            self.db.query(View)
            .filter(View.item_type == item_type, View.owner == None)
            .all()
        )
        return [ViewSchema.model_validate(f) for f in views]

    def update_view(self, view_id: str, field_name: str, field_val) -> ViewSchema:
        self.db.query(View).filter(View.id == view_id).update(
            {field_name: field_val}, synchronize_session=False
        )
        self.db.commit()
        view = self.db.query(View).filter(View.id == view_id).first()
        return ViewSchema.model_validate(view)

    def insert_views_query(
        self, loggedin_user_id: str, new_views: List[CreateViewSchema]
    ) -> List[ViewSchema]:
        views = [
            View(
                title=new_view.title,
                item_type=new_view.item_type,
                owner=loggedin_user_id,
                view_as=new_view.view_as,
                filters=new_view.filters.model_dump() if new_view.filters else None,
                group_by=new_view.group_by,
                sort_by=new_view.sort_by,
                status=new_view.status,
            )
            for new_view in new_views
        ]
        self.db.add_all(views)
        self.db.commit()
        for view in views:
            self.db.refresh(view)
        return [ViewSchema.model_validate(f) for f in views]

    def update_full_view_query(self, view_id: str, full_view: ViewSchema) -> ViewSchema:
        full_view_dict = full_view.dict(exclude_unset=True)

        self.db.query(View).filter(
            View.id == view_id,
        ).update(full_view_dict, synchronize_session=False)
        self.db.commit()

        view = self.db.query(View).filter(View.id == view_id).first()
        return ViewSchema.model_validate(view)

    def delete_view(self, view_id: str) -> None:
        record = self.db.query(View).filter(View.id == view_id).first()

        if record:
            self.db.delete(record)
            self.db.commit()
        return None
