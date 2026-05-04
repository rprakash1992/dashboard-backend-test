from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.repositories.database_dashboard.base import BaseRepository
from app.schemas.item import NewItemSchema, ItemSchema, ItemType
from app.models.item import Item


class ItemRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_items_by_title(self, title: str) -> List[ItemSchema]:
        items = self.db.query(Item).filter(Item.title == title).all()
        return [ItemSchema.model_validate(f) for f in items]

    def get_items_by_item_type(self, item_type: ItemType) -> List[ItemSchema]:
        items = (
            self.db.query(Item)
            .filter(Item.item_type == item_type, Item.deleted_at == None)
            .all()
        )
        return [ItemSchema.model_validate(f) for f in items]

    def get_item_by_id(self, id: str) -> ItemSchema:
        item = (
            self.db.query(Item).filter(Item.id == id, Item.deleted_at == None).first()
        )
        return ItemSchema.model_validate(item)

    def get_items_by_ids(self, ids: List[str]) -> List[ItemSchema]:
        items = (
            self.db.query(Item).filter(Item.id.in_(ids), Item.deleted_at == None).all()
        )
        return [ItemSchema.model_validate(f) for f in items]

    def get_items_by_title_and_item_type(
        self, title: str, item_type: ItemType
    ) -> List[ItemSchema]:
        items = (
            self.db.query(Item)
            .filter(
                Item.title == title,
                Item.item_type == item_type,
                Item.deleted_at == None,
            )
            .all()
        )
        return [ItemSchema.model_validate(f) for f in items]

    def get_item_by_system_key(self, system_key: str) -> ItemSchema:
        item = self.db.query(Item).filter(Item.system_key == system_key).first()
        return ItemSchema.model_validate(item)

    def get_items_by_ids_and_item_type(
        self, ids: List[str], item_type: ItemType
    ) -> List[ItemSchema]:
        items = (
            self.db.query(Item)
            .filter(
                Item.id.in_(ids), Item.item_type == item_type, Item.deleted_at == None
            )
            .all()
        )
        return [ItemSchema.model_validate(f) for f in items]

    def get_items_by_ids_and_item_type_and_title_ilike(
        self, ids: List[str], item_type: ItemType, search_text: str
    ) -> List[ItemSchema]:
        search_text = search_text.strip('"')
        search_pattern = f"%{search_text}%"
        items = (
            self.db.query(Item)
            .filter(
                Item.id.in_(ids),
                Item.item_type == item_type,
                Item.title.ilike(search_pattern),
                Item.deleted_at == None,
            )
            .all()
        )
        return [ItemSchema.model_validate(f) for f in items]

    def get_items_by_item_type_and_title_ilike(
        self, item_type: ItemType, search_text: str
    ) -> List[ItemSchema]:
        search_text = search_text.strip('"')
        search_pattern = f"%{search_text}%"
        items = (
            self.db.query(Item)
            .filter(
                Item.item_type == item_type,
                Item.title.ilike(search_pattern),
                Item.deleted_at == None,
            )
            .limit(5)
            .all()
        )
        return [ItemSchema.model_validate(f) for f in items]

    def update_full_item(self, item: ItemSchema) -> ItemSchema:
        self.db.query(Item).filter(Item.id == item.id).update(
            {
                "title": item.title,
                "description": item.description,
                "image": item.image,
                "tags": item.tags,
                "last_modified_at": datetime.now(timezone.utc),
            },
            synchronize_session=False,
        )

        self.db.commit()
        updated_item = self.db.query(Item).filter(Item.id == item.id).first()
        return ItemSchema.model_validate(updated_item)

    def update_item_by_id_and_item_type(
        self, id: str, item_type: ItemType, field_name: str, field_val
    ) -> ItemSchema:
        self.db.query(Item).filter(Item.id == id, Item.item_type == item_type).update(
            {field_name: field_val, "last_modified_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )
        self.db.commit()

        item = self.db.query(Item).filter(Item.id == id).first()
        return ItemSchema.model_validate(item)

    def insert_items(self, new_items: List[NewItemSchema]) -> List[ItemSchema]:
        items = [
            Item(
                title=new_item.title,
                description=new_item.description,
                image=new_item.image,
                tags=new_item.tags,
                item_type=new_item.item_type,
            )
            for new_item in new_items
        ]

        self.db.add_all(items)
        self.db.commit()

        for item in items:
            self.db.refresh(item)
        return [ItemSchema.model_validate(f) for f in items]
