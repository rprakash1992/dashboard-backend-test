from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any

# import core
from app.core.config import get_settings

# import repositories
from app.repositories.database_dashboard.job import JobRepository
from app.repositories.database_dashboard.workflow import WorkflowRepository

# import schemas
from app.schemas.job import JobSchema, InsertJobResponse, JobType, JobResponseSchema
from app.schemas.relation import RelationSchema, RelationType
from app.schemas.item import ItemType, NewItemSchema

# import services
from app.services.role import RoleService
from app.services.relation import RelationService
from app.services.item import ItemService
from app.services.argo_client import ArgoClientService

settings = get_settings()


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = JobRepository(db)
        self.workflow_repo = WorkflowRepository(db)
        self.relation_service = RelationService(db)
        self.item_service = ItemService(db)
        self.argo_client = ArgoClientService()

    def insert_job(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        job_type: JobType,
        run_id: Optional[str] = None,
        total_steps: Optional[str] = None,
        completed_steps: Optional[str] = None,
    ) -> InsertJobResponse:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_create_permission = role_service.has_create_item_permission(ItemType.JOB)

        if not has_create_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to create job in this workspace.",
            )

        item = NewItemSchema(
            title=title,
            item_type=ItemType.JOB,
            description=description,
            image=image,
            tags=tags,
        )
        new_item_response = self.item_service.insert_item(
            selected_workspace_id, loggedin_user_id, item
        )
        new_item_id = new_item_response.id

        job = JobSchema(
            id=new_item_id,
            job_type=job_type,
            run_id=run_id,
            total_steps=total_steps,
            completed_steps=completed_steps,
        )
        new_job_response = self.repo.insert_jobs([job])
        return InsertJobResponse(item=new_item_response, job=new_job_response[0])

    async def create_job_from_workflow(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        workflow_id: str,
        workflow_parameters: dict,
    ) -> InsertJobResponse:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_create_permission = role_service.has_create_item_permission(ItemType.JOB)

        if not has_create_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to create job in this workspace.",
            )

        flow_record = self.workflow_repo.get_workflow_by_id(workflow_id)
        if not flow_record:
            raise HTTPException(status_code=404, detail="Flow not found.")

        workflow_status = flow_record.status
        if workflow_status == "pending":
            raise HTTPException(status_code=400, detail="Workflow is not active yet.")

        workflow_validity = flow_record.is_valid
        if not workflow_validity:
            raise HTTPException(status_code=400, detail="Workflow is not valid.")

        flow_run = await self.argo_client.trigger_user_flow(
            settings.aws_s3_bucket, flow_record.s3_key, workflow_parameters
        )
        insert_job_response = self.insert_job(
            selected_workspace_id,
            loggedin_user_id,
            title,
            description,
            image,
            tags,
            JobType.WORKFLOW_RUN,
            str(flow_run.id),
            "0",
            "0",
        )

        item = insert_job_response.item
        job = insert_job_response.job
        new_item_id = item.id

        new_relation = RelationSchema(
            source_id=workflow_id, target_id=new_item_id, relation=RelationType.JOB
        )
        self.relation_service.insert_relation(new_relation)

        return InsertJobResponse(item=item, job=job)

    async def fetch_jobs_by_ids(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        job_ids: List[str],
    ) -> List[JobResponseSchema]:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.JOB
        )

        if not has_read_contents_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to access job content in this workspace.",
            )

        jobs = self.repo.get_jobs_by_ids(job_ids)
        response = []
        for job in jobs:
            run_id = job.run_id
            run = await self.argo_client.get_flow_run(run_id)
            response.append(
                JobResponseSchema(
                    id=job.id,
                    job_type=job.job_type,
                    total_steps=job.total_steps,
                    completed_steps=job.completed_steps,
                    run_id=run_id,
                    run_details=run,
                    output_item_id=None,
                )
            )
        return response

    async def get_job_by_output_item_id(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        output_item_id: str,
    ) -> JobResponseSchema:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_content_permission = role_service.has_read_content_permission(
            ItemType.PROJECT
        )

        if not has_read_content_permission:
            return []

        relations = self.relation_service.fetch_relations_by_target_id_and_relation(
            output_item_id,
            RelationType.JOB_OUTPUT,
        )

        if len(relations) <= 0:
            return {}

        relation = relations[0]
        job_id = relation.source_id

        job = self.repo.get_job_by_id(job_id)
        run_id = job.run_id

        flow_run = await self.argo_client.get_flow_run(run_id)

        return JobResponseSchema(
            id=job.id,
            job_type=job.job_type,
            total_steps=job.total_steps,
            completed_steps=job.completed_steps,
            run_id=run_id,
            run_details=flow_run,
            output_item_id=output_item_id,
        )

    async def get_job_id_by_output_item_id(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        output_item_id: str,
    ) -> str:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_content_permission = role_service.has_read_content_permission(
            ItemType.PROJECT
        )

        if not has_read_content_permission:
            return []

        relations = self.relation_service.fetch_relations_by_target_id_and_relation(
            output_item_id,
            RelationType.JOB_OUTPUT,
        )

        if len(relations) <= 0:
            return {}

        relation = relations[0]
        job_id = relation.source_id
        return job_id

    def update_job_field_by_id(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        job_id: str,
        field_name: str,
        field_val: Any,
    ) -> JobSchema | None:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_update_contents_permission = role_service.has_update_content_permission(
            ItemType.JOB
        )

        if not has_update_contents_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to update job content in this workspace.",
            )

        return self.repo.update_job_by_id(job_id, field_name, field_val)
