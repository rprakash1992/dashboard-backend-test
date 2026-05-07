from fastapi import HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Any
from uuid import uuid4

# import core
from app.core.config import get_settings

# import repositories
from app.repositories.database_dashboard.workflow import WorkflowRepository
from app.repositories.database_dashboard.job import JobRepository

# import schemas
from app.schemas.workflow import WorkflowSchema, InsertWorkflowResponse
from app.schemas.relation import RelationSchema, RelationType
from app.schemas.item import ItemType, NewItemSchema, ItemSchema
from app.schemas.job import JobSchema, JobType

# import services
from app.services.role import RoleService
from app.services.relation import RelationService
from app.services.item import ItemService
from app.services.argo_client import ArgoClientService

settings = get_settings()


class PrepareWorkflowCreationResponse(BaseModel):
    output_workflow_item: ItemSchema
    output_workflow: WorkflowSchema
    job_item_id: str
    s3_key: str


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = WorkflowRepository(db)
        self.job_repo = JobRepository(db)
        self.relation_service = RelationService(db)
        self.item_service = ItemService(db)
        self.prefect_client_service = ArgoClientService()

    def fetch_workflows_by_ids(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        workflows_ids: List[str],
    ) -> List[WorkflowSchema]:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_content_permission = role_service.has_read_content_permission(
            ItemType.WORKFLOW
        )

        if not has_read_content_permission:
            return []

        return self.repo.get_workflows_by_ids(workflows_ids)

    def _insert_job(
        self,
        loggedin_user_id: str,
        selected_workspace_id: str,
        item_title: str,
        input_file_id: str,
        output_workflow_item_id: str,
    ) -> str:
        # add a new job item in items table
        new_item = NewItemSchema(
            title=f"Create Workflow-{item_title}",
            item_type=ItemType.JOB,
        )
        added_item = self.item_service.insert_item(
            selected_workspace_id,
            loggedin_user_id,
            new_item,
        )
        new_job_item_id = added_item.id

        # add new job in jobs table corresponding to the above job item
        new_job = JobSchema(
            id=new_job_item_id,
            job_type=JobType.ZIP_TO_WORKFLOW,
            total_steps="8",
            completed_steps="0",
        )
        self.job_repo.insert_jobs([new_job])

        # add relation between the zip file item which was extracted and the job item
        zip_job_relation = RelationSchema(
            source_id=input_file_id,
            target_id=new_job_item_id,
            relation=RelationType.JOB,
        )
        # add relation between the job and the workflow item
        job_folder_relation = RelationSchema(
            source_id=new_job_item_id,
            target_id=output_workflow_item_id,
            relation=RelationType.JOB_OUTPUT,
        )

        self.relation_service.insert_relation(zip_job_relation)
        self.relation_service.insert_relation(job_folder_relation)
        return new_job_item_id

    def _prepare_workflow_creation(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        file_id: str,
        variables: dict,
    ) -> PrepareWorkflowCreationResponse:
        # insert new item to show workflow item in frontend
        new_item_to_add = NewItemSchema(
            title=title,
            item_type=ItemType.WORKFLOW,
            description=description,
            image=image,
            tags=tags,
        )
        output_workflow_item = self.item_service.insert_item(
            selected_workspace_id, loggedin_user_id, new_item_to_add
        )
        output_workflow_item_id = output_workflow_item.id

        # insert new workflow in workflows table corresponding to the item inserted above
        new_s3_key = str(uuid4())
        new_workflow_to_add = WorkflowSchema(
            id=output_workflow_item_id,
            s3_key=new_s3_key,
            flow_function_name=settings.FLOW_FUNCTION_NAME,
            status="pending",
            parameter_schema=variables,
        )

        insert_workflow_response = self.repo.insert_workflows([new_workflow_to_add])
        output_workflow = insert_workflow_response[0]

        job_item_id = self._insert_job(
            loggedin_user_id,
            selected_workspace_id,
            title,
            file_id,
            output_workflow_item_id,
        )

        return PrepareWorkflowCreationResponse(
            output_workflow_item=output_workflow_item,
            output_workflow=output_workflow,
            job_item_id=job_item_id,
            s3_key=new_s3_key,
        )

    async def create_workflow(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        file_id: str,
        variables: dict,
    ) -> InsertWorkflowResponse:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_create_permission = role_service.has_create_item_permission(
            ItemType.WORKFLOW
        )

        if not has_create_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to create workflow in this workspace.",
            )

        result = self._prepare_workflow_creation(
            selected_workspace_id,
            loggedin_user_id,
            title,
            description,
            image,
            tags,
            file_id,
            variables,
        )
        output_workflow = result.output_workflow
        output_workflow_item = result.output_workflow_item
        output_workflow_item_id = output_workflow_item.id
        job_item_id = result.job_item_id
        # s3_key = result.s3_key

        deployment_id = "extract-zip-workflow-with-folder-structure"

        flow_run = await self.prefect_client_service.trigger_extract_zip_with_folder_structure_flow(
            deployment_id,
            loggedin_user_id=loggedin_user_id,
            selected_workspace_id=selected_workspace_id,
            input_item_id=file_id,
            output_item_id=output_workflow_item_id,
        )

        if flow_run.id:
            self.job_repo.update_job_by_id(
                job_item_id,
                "run_id",
                flow_run.id,
            )

            return InsertWorkflowResponse(
                item=output_workflow_item,
                workflow=output_workflow,
            )

    def update_workflow(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        workflow: WorkflowSchema,
    ):
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_update_contents_permission = role_service.has_update_content_permission(
            ItemType.WORKFLOW
        )

        if not has_update_contents_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to update workflow content in this workspace.",
            )

        return self.repo.update_workflow_record(workflow)
