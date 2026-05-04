from sqlalchemy.orm import Session
from app.repositories.database_dashboard.base import BaseRepository
from app.models.user_flow import UserFlow
from app.schemas.user_flow import UserFlowSchema


class UserFlowRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def insert_user_flow_query(self, new_flow: UserFlowSchema) -> UserFlowSchema:
        user_flow = UserFlow(
            id=new_flow.id,
            s3_key=new_flow.s3_key,
            flow_function_name=new_flow.flow_function_name,
            deployment_id=new_flow.deployment_id,
            deployment_name=new_flow.deployment_name,
            flow_id=new_flow.flow_id,
        )
        self.db.add(user_flow)
        self.db.commit()
        self.db.refresh(user_flow)
        return UserFlowSchema.model_validate(user_flow)

    def get_user_flow_by_id_query(self, flow_id: str) -> UserFlowSchema:
        user_flow = (
            self.db.query(UserFlow)
            .filter(
                UserFlow.id == flow_id,
            )
            .first()
        )
        return UserFlowSchema.model_validate(user_flow)
