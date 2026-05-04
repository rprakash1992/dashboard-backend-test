from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

# import repositories
from app.repositories.database_dashboard.relation import RelationRepository

# import schemas
from app.schemas.relation import RelationSchema


class RelationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RelationRepository(db)

    def insert_relation(
        self,
        new_relation: RelationSchema,
    ) -> List[RelationSchema]:
        # check if the relation already exists
        relations = self.repo.get_relation_by_sourceid_targetid_relation(
            new_relation.source_id, new_relation.target_id, new_relation.relation
        )

        if len(relations) > 0:
            raise HTTPException(status_code=400, detail="Relation already exists.")

        return self.repo.insert_relations([new_relation])

    def fetch_relations_by_source_id_and_relation(
        self,
        source_id: str,
        relation: str,
    ) -> List[RelationSchema]:
        if relation == "role":
            return self.repo.get_relations_by_source_id_ilike_relation(
                source_id, f"%{relation}%"
            )

        else:
            return self.repo.get_relations_by_source_id_and_relation(
                source_id, relation
            )

    def fetch_relations_by_target_id_and_relation(
        self,
        target_id: str,
        relation: str,
    ) -> List[RelationSchema]:
        if relation == "role":
            return self.repo.get_relations_by_target_id_ilike_relation(
                target_id, f"%{relation}%"
            )

        else:
            return self.repo.get_relations_by_target_id_and_relation(
                target_id, relation
            )

    def fetch_relations_by_source_id_and_target_ids(
        self,
        source_id: str,
        target_ids: List[str],
    ) -> List[RelationSchema]:
        return self.repo.get_relations_by_source_id_and_target_ids(
            source_id, target_ids
        )
