from sqlalchemy.orm import Session
from typing import List
from app.schemas.tag import CreateTagSchema, TagSchema
from app.repositories.database_dashboard.base import BaseRepository
from app.models.tag import Tag


class TagRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_all_tags(self) -> List[TagSchema]:
        tags = self.db.query(Tag).all()
        return [TagSchema.model_validate(f) for f in tags]

    def insert_tags(self, new_tags: List[CreateTagSchema]) -> List[TagSchema]:
        tags = [
            Tag(
                name=new_tag.name,
                description=new_tag.description,
            )
            for new_tag in new_tags
        ]

        self.db.add_all(tags)
        self.db.commit()

        for tag in tags:
            self.db.refresh(tag)
        return [TagSchema.model_validate(f) for f in tags]
