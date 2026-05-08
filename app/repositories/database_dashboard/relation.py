from sqlalchemy.orm import Session
from typing import List
from app.schemas.relation import RelationSchema
from app.repositories.database_dashboard.base import BaseRepository
from app.models.relation import Relation


class RelationRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_relations_by_source_id(self, source_id: str) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation).filter(Relation.source_id == source_id).all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_target_id(self, target_id: str) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation).filter(Relation.target_id == target_id).all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_relation(self, relation: str) -> List[RelationSchema]:
        relations = self.db.query(Relation).filter(Relation.relation == relation).all()
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_target_ids(
        self, target_ids: List[str]
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation).filter(Relation.target_id.in_(target_ids)).all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_id_and_relation(
        self, source_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id == source_id, Relation.relation == relation)
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_target_id_and_relation(
        self, target_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.target_id == target_id, Relation.relation == relation)
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_id_and_target_id(
        self, source_id: str, target_id: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id == source_id, Relation.target_id == target_id)
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_ids_and_target_id(
        self, source_ids: List[str], target_id: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id.in_(source_ids), Relation.target_id == target_id)
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_id_and_target_ids(
        self, source_id: str, target_ids: List[str]
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id == source_id, Relation.target_id.in_(target_ids))
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_id_target_ids_relation(
        self, source_id: str, target_ids: List[str], relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(
                Relation.source_id == source_id,
                Relation.target_id.in_(target_ids),
                Relation.relation == relation,
            )
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_id_and_not_relation(
        self, source_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id == source_id, Relation.relation != relation)
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_ids_and_not_relation(
        self, source_ids: List[str], relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id.in_(source_ids), Relation.relation != relation)
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relation_by_sourceid_targetid_relation(
        self, source_id: str, target_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(
                Relation.source_id == source_id,
                Relation.target_id == target_id,
                Relation.relation == relation,
            )
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relation_by_sourceids_targetid_relation(
        self, source_ids: List[str], target_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(
                Relation.source_id.in_(source_ids),
                Relation.target_id == target_id,
                Relation.relation == relation,
            )
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    # def get_relations_by_source_id_and_ilike_relation(
    #     self, source_id: str, relation: str
    # ) -> List[RelationSchema]:
    #     relations = (
    #         self.db.query(Relation)
    #         .filter(
    #             Relation.source_id == source_id,
    #             Relation.relation.ilike(relation),
    #         )
    #         .all()
    #     )
    #     return [RelationSchema.model_validate(f) for f in relations]

    def get_relation_by_sourceids_not_targetid_ilike_relation(
        self, source_ids: List[str], target_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(
                Relation.source_id.in_(source_ids),
                Relation.target_id != target_id,
                Relation.relation.ilike(relation),
            )
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relation_by_sourceid_targetid_ilike_relation(
        self, source_id: str, target_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(
                Relation.source_id == source_id,
                Relation.target_id == target_id,
                Relation.relation.ilike(relation),
            )
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_source_id_ilike_relation(
        self, source_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id == source_id, Relation.relation.ilike(relation))
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def get_relations_by_target_id_ilike_relation(
        self, target_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.target_id == target_id, Relation.relation.ilike(relation))
            .all()
        )
        return [RelationSchema.model_validate(f) for f in relations]

    def update_relation(
        self, source_id: str, target_id: str, relation: str
    ) -> List[RelationSchema]:
        relations = (
            self.db.query(Relation)
            .filter(Relation.source_id == source_id, Relation.target_id == target_id)
            .all()
        )
        for r in relations:
            r.relation = relation
        self.db.commit()
        for r in relations:
            self.db.refresh(r)
        return [RelationSchema.model_validate(r) for r in relations]

    def insert_relations(self, relations: List[RelationSchema]) -> List[RelationSchema]:
        new_relations = [
            Relation(
                source_id=relation.source_id,
                target_id=relation.target_id,
                relation=relation.relation,
            )
            for relation in relations
        ]

        self.db.add_all(new_relations)
        self.db.commit()

        for relation in new_relations:
            self.db.refresh(relation)
        return [RelationSchema.model_validate(f) for f in new_relations]
