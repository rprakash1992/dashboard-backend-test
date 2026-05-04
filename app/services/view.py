from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Any

# import repositories
from app.repositories.database_dashboard.view import ViewRepository

# import schemas
from app.schemas.view import ViewSchema, CreateViewSchema


restricted_view_titles = ["all", "uploads", "workflows"]


class ViewService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ViewRepository(db)

    def fetch_dashboard_views(
        self,
        loggedin_user_id: str,
        selected_item_type: str,
    ) -> List[ViewSchema]:
        views_data = []

        if selected_item_type:
            response1 = self.repo.get_views_by_item_type_and_owner(
                selected_item_type, loggedin_user_id
            )
            response2 = self.repo.get_views_by_item_type_and_null_owner(
                selected_item_type
            )

            views_data = response1 + response2
        else:
            response1 = self.repo.get_views_by_owner(loggedin_user_id)
            response2 = self.repo.get_views_by_null_owner()

            views_data = response1 + response2

        return views_data

    def insert_view(
        self, loggedin_user_id: str, new_view: CreateViewSchema
    ) -> List[ViewSchema]:
        view_title = new_view.title

        is_restricted_view = any(
            item.lower() == view_title.strip().lower()
            for item in restricted_view_titles
        )

        if is_restricted_view:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create a view with title '{view_title}'",
            )

        return self.repo.insert_views_query(loggedin_user_id, [new_view])

    def delete_view_by_id(self, loggedin_user_id: str, view_id: str) -> None:
        views = self.repo.get_views_by_id_and_owner(view_id, loggedin_user_id)

        if len(views) == 0:
            raise HTTPException(status_code=400, detail="Invalid View Id.")

        view = views[0]
        view_title: str = view.title

        is_restricted_view = any(
            item.lower() == view_title.strip().lower()
            for item in restricted_view_titles
        )

        if not view.owner or is_restricted_view:
            raise HTTPException(status_code=400, detail="This View cannot be deleted.")

        if str(view.owner) != str(loggedin_user_id):
            raise HTTPException(
                status_code=401, detail="You are not authorized to delete this View."
            )

        return self.repo.delete_view(view_id)

    def update_view_by_id(
        self,
        loggedin_user_id: str,
        view_id: str,
        updated_field_name: str,
        updated_field_value: Any,
    ) -> ViewSchema:
        if updated_field_name == "title":
            view_title: str = updated_field_value

            if view_title.strip().lower() == "all":
                raise HTTPException(
                    status_code=401,
                    detail=f"Cannot create a view with title '{view_title}'",
                )

        views = self.repo.get_views_by_id_and_owner(view_id, loggedin_user_id)

        if len(views) == 0:
            raise HTTPException(status_code=401, detail="Invalid View Id.")

        view = views[0]

        if str(view.owner) != str(loggedin_user_id):
            raise HTTPException(
                status_code=401, detail="You are not authorized to update this View."
            )

        return self.repo.update_view(view_id, updated_field_name, updated_field_value)

    def update_full_view(
        self, loggedin_user_id: str, view_id: str, view_to_update: ViewSchema
    ) -> ViewSchema:
        views = self.repo.get_views_by_id_and_owner(view_id, loggedin_user_id)

        if len(views) == 0:
            raise HTTPException(status_code=401, detail="Invalid View Id.")

        view = views[0]

        if str(view.owner) != str(loggedin_user_id):
            raise HTTPException(
                status_code=401, detail="You are not authorized to update this View."
            )

        return self.repo.update_full_view_query(view_id, view_to_update)
