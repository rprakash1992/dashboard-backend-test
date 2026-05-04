from sqlalchemy.orm import Session
from typing import List

# import models
from app.models.workflow import Workflow

# import repositories
from app.repositories.database_dashboard.base import BaseRepository

# import schemas
from app.schemas.workflow import WorkflowSchema


class WorkflowRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_workflow_by_id(self, flow_id: str):
        workflow = (
            self.db.query(Workflow)
            .filter(
                Workflow.id == flow_id,
            )
            .first()
        )
        if not workflow:
            return None

        return WorkflowSchema.model_validate(workflow)

    def get_workflows_by_ids(self, workflows_ids: List[str]):
        workflows = self.db.query(Workflow).filter(Workflow.id.in_(workflows_ids)).all()
        return [WorkflowSchema.model_validate(f) for f in workflows]

    def update_workflow_record(self, workflow: WorkflowSchema) -> WorkflowSchema:
        self.db.query(Workflow).filter(Workflow.id == workflow.id).update(
            workflow.model_dump(exclude_unset=True), synchronize_session=False
        )
        self.db.commit()
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow.id).first()
        return WorkflowSchema.model_validate(workflow)

    def insert_workflows(
        self, new_workflows: List[WorkflowSchema]
    ) -> List[WorkflowSchema]:
        workflows = [
            Workflow(
                id=new_workflow.id,
                s3_key=new_workflow.s3_key,
                flow_function_name=new_workflow.flow_function_name,
                deployment_id=new_workflow.deployment_id,
                deployment_name=new_workflow.deployment_name,
                flow_id=new_workflow.flow_id,
                status=new_workflow.status,
                is_valid=new_workflow.is_valid,
                parameter_schema=new_workflow.parameter_schema,
            )
            for new_workflow in new_workflows
        ]
        self.db.add_all(workflows)
        self.db.commit()
        for project in workflows:
            self.db.refresh(project)
        return [WorkflowSchema.model_validate(f) for f in workflows]
