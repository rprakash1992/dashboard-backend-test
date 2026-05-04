from sqlalchemy.orm import Session
from typing import List

# import repositories
from app.repositories.database_dashboard.tag import TagRepository

# import schemas
from app.schemas.tag import CreateTagSchema, TagSchema


class TagService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TagRepository(db)

    def fetch_all_tags(self) -> List[TagSchema]:
        return self.repo.get_all_tags()

    def insert_tags(self, new_tags: List[CreateTagSchema]) -> List[TagSchema]:
        all_tags = self.repo.get_all_tags()

        payload: List[CreateTagSchema] = []

        for new_tag in new_tags:
            # check if a tag with the same name alreagy exists
            if not any(
                tag.get("name").lower() == new_tag.name.lower() for tag in all_tags
            ):
                payload.append(new_tag)

        return self.repo.insert_tags(payload)
