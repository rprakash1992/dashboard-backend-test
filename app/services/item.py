from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Any

# import repositories
from app.repositories.database_dashboard.tag import TagRepository
from app.repositories.database_dashboard.role import RoleRepository
from app.repositories.database_dashboard.item import ItemRepository
from app.repositories.database_dashboard.relation import RelationRepository

# import schemas
from app.schemas.relation import RelationSchema, RelationType
from app.schemas.tag import CreateTagSchema

# import services
from app.services.s3_client import S3ClientService
from app.services.role import RoleService
from app.schemas.item import (
    NewItemSchema,
    ItemSchema,
    ItemType,
    FileTraceabilityData,
    ProjectTraceabilityData,
    ReportTraceabilityData,
    JobTraceabilityData,
    WorkflowTraceabilityData,
    TraceabilityRespSchema,
)

# import utils
from app.utils.misc import get_current_time


class ItemService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ItemRepository(db)
        self.relation_repo = RelationRepository(db)
        self.role_repo = RoleRepository(db)
        self.tag_repo = TagRepository(db)
        self.s3_client = S3ClientService()

    def _insert_tags(self, new_tags: List[str]) -> None:
        all_tags = self.tag_repo.get_all_tags()

        new_tag = ""

        for t in new_tags:
            if not any(tag.name.lower() == t.lower() for tag in all_tags):
                new_tag = t

        if new_tag:
            payload = CreateTagSchema(name=new_tag, description="")
            self.tag_repo.insert_tags([payload])

    def _fetch_file_traceability(self, item_id: str) -> TraceabilityRespSchema:
        relation_resp = self.relation_repo.get_relations_by_source_id_and_relation(
            item_id, RelationType.DEPENDENT
        )
        report_items_ids = [relation.target_id for relation in relation_resp]
        report_items_resp = self.repo.get_items_by_ids(report_items_ids)

        file_traceability_data = FileTraceabilityData(projects=report_items_resp)
        return TraceabilityRespSchema(
            item_type=ItemType.FILE, traceability_data=file_traceability_data
        )

    def _fetch_project_traceability(self, item_id: str) -> TraceabilityRespSchema:
        relation_resp1 = self.relation_repo.get_relations_by_source_id_and_relation(
            item_id, RelationType.DEPENDENT
        )
        relation_resp2 = self.relation_repo.get_relations_by_target_id_and_relation(
            item_id, RelationType.DEPENDENT
        )

        report_items_ids = [relation.target_id for relation in relation_resp1]
        file_items_ids = [relation.source_id for relation in relation_resp2]

        report_items_resp = self.repo.get_items_by_ids(report_items_ids)
        file_items_resp = self.repo.get_items_by_ids(file_items_ids)

        project_traceability_data = ProjectTraceabilityData(
            files=file_items_resp,
            reports=report_items_resp,
        )
        return TraceabilityRespSchema(
            item_type=ItemType.PROJECT, traceability_data=project_traceability_data
        )

    def _fetch_report_traceability(self, item_id: str) -> TraceabilityRespSchema:
        relation_resp = self.relation_repo.get_relations_by_target_id_and_relation(
            item_id, RelationType.DEPENDENT
        )
        project_items_ids = [relation.source_id for relation in relation_resp]
        project_items_resp = self.repo.get_items_by_ids(project_items_ids)
        report_traceability_data = ReportTraceabilityData(projects=project_items_resp)
        return TraceabilityRespSchema(
            item_type=ItemType.REPORT, traceability_data=report_traceability_data
        )

    def _fetch_job_traceability(self, item_id: str) -> TraceabilityRespSchema:
        relation_resp1 = self.relation_repo.get_relations_by_target_id_and_relation(
            item_id, RelationType.JOB
        )
        relation_resp2 = self.relation_repo.get_relations_by_source_id_and_relation(
            item_id, RelationType.JOB_OUTPUT
        )

        ids = []
        if len(relation_resp1) > 0:
            relation1 = relation_resp1[0]
            job_input_item_id = relation1.source_id
            ids.append(job_input_item_id)

        if len(relation_resp2) > 0:
            relation2 = relation_resp2[0]
            job_output_item_id = relation2.target_id
            ids.append(job_output_item_id)

        items_resp = self.repo.get_items_by_ids(ids)
        job_traceability_data = JobTraceabilityData(
            inputs=[items_resp[0]] if len(items_resp) > 0 else [],
            outputs=[items_resp[1]] if len(items_resp) > 1 else [],
        )
        return TraceabilityRespSchema(
            item_type=ItemType.JOB, traceability_data=job_traceability_data
        )

    def _fetch_workflow_traceability(self, item_id: str) -> TraceabilityRespSchema:
        relation_resp1 = self.relation_repo.get_relations_by_target_id_and_relation(
            item_id, RelationType.JOB_OUTPUT
        )
        relation_resp2 = self.relation_repo.get_relations_by_source_id_and_relation(
            item_id, RelationType.JOB
        )

        ids = []
        if len(relation_resp1) > 0:
            relation1 = relation_resp1[0]
            input_item_id = relation1.source_id
            ids.append(input_item_id)

        if len(relation_resp2) > 0:
            relation2 = relation_resp2[0]
            output_item_id = relation2.target_id
            ids.append(output_item_id)

        items_resp = self.repo.get_items_by_ids(ids)
        job_traceability_data = WorkflowTraceabilityData(
            inputs=[items_resp[0]] if len(items_resp) > 0 else [],
            outputs=[items_resp[1]] if len(items_resp) > 1 else [],
        )
        return TraceabilityRespSchema(
            item_type=ItemType.JOB, traceability_data=job_traceability_data
        )

    def fetch_item_traceability(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
    ) -> TraceabilityRespSchema:
        items_resp = self.repo.get_items_by_ids([item_id])
        item = items_resp[0]
        item_type = item.item_type

        # check if user has read items permission in the selected workspace
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_items_permission = role_service.has_read_items_permission(item_type)

        if not has_read_items_permission:
            raise HTTPException(
                status_code=403,
                detail="You don't have the permission to read items in this workspace.",
            )

        # check if the item is present in the selected workspace
        resp = self.relation_repo.get_relation_by_sourceid_targetid_relation(
            selected_workspace_id, item_id, RelationType.CHILD
        )
        is_item_present_in_workspace = len(resp) > 0

        if not is_item_present_in_workspace:
            raise HTTPException(status_code=404, detail="Item not found.")

        if item_type == ItemType.FILE:
            if not role_service.has_read_content_permission(ItemType.PROJECT):
                raise HTTPException(
                    status_code=403,
                    detail="You don't have the permission access file traceability.",
                )
            return self._fetch_file_traceability(item_id)

        if item_type == ItemType.PROJECT:
            if not (
                role_service.has_read_content_permission(ItemType.PROJECT)
                and role_service.has_read_content_permission(ItemType.REPORT)
            ):
                raise HTTPException(
                    status_code=403,
                    detail="You don't have the permission access project traceability.",
                )
            return self._fetch_project_traceability(item_id)

        if item_type == ItemType.REPORT:
            if not role_service.has_read_content_permission(ItemType.REPORT):
                raise HTTPException(
                    status_code=403,
                    detail="You don't have the permission access report traceability.",
                )
            return self._fetch_report_traceability(item_id)

        if item_type == ItemType.JOB:
            return self._fetch_job_traceability(item_id)

        if item_type == ItemType.WORKFLOW:
            return self._fetch_workflow_traceability(item_id)

        raise HTTPException(
            status_code=404, detail="No traceability found for this item."
        )

    def _fetch_user_profile_items(
        self, selected_workspace_id, loggedin_user_id
    ) -> List[ItemSchema]:
        # If item_type is "user_profile" and selected_workspace is "admin" and role of loggedin user is "system_administrator"
        # then we need to return all user profile, because system_administrator can change the profile status to active/inactive

        # get id of system_administrator_workspace item
        admin_workspace_item = self.repo.get_item_by_system_key(
            "system_administrator_workspace"
        )
        admin_workspace_id = admin_workspace_item.id

        # get id of system_administrator role
        system_admin_role_item = self.repo.get_item_by_system_key(
            "system_administrator_role"
        )
        system_admin_role_item_id = system_admin_role_item.id

        # check if role of loggedin user in selected workspace is of system administrator
        relation_response = (
            self.relation_repo.get_relation_by_sourceid_targetid_relation(
                selected_workspace_id,
                loggedin_user_id,
                f"role.{system_admin_role_item_id}",
            )
        )
        is_loggedin_user_a_system_administrator = len(relation_response) > 0
        is_selected_ws_system_admin_ws = selected_workspace_id == admin_workspace_id

        if is_selected_ws_system_admin_ws and is_loggedin_user_a_system_administrator:
            # means selected workspace is "system_administrator_workspace"
            # and role of loggedin user is "system_administrator_role"
            all_user_profiles = self.repo.get_items_by_item_type(ItemType.USERPROFILE)
            return all_user_profiles
        else:
            relation_response = (
                self.relation_repo.get_relations_by_source_id_ilike_relation(
                    selected_workspace_id, "%role%"
                )
            )
            target_user_profile_ids = [
                relation.target_id for relation in relation_response
            ]
            return self.repo.get_items_by_ids(target_user_profile_ids)

    def fetch_dashboard_items(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        selected_item_type: str,
    ) -> List[ItemSchema]:
        if selected_item_type == ItemType.ROLE:
            # if item_type is "role" then return all roles without checking any permission
            return self.repo.get_items_by_item_type(ItemType.ROLE)

        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_items_permission = role_service.has_read_items_permission(
            selected_item_type
        )

        if not has_read_items_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have the permission to view {selected_item_type}s in this workspace.",
            )

        # if selected_item_type == ItemType.USERPROFILE:
        #     return self._fetch_user_profile_items(
        #         selected_workspace_id, loggedin_user_id
        #     )

        if selected_item_type == ItemType.USERPROFILE:
            relation_response = (
                self.relation_repo.get_relations_by_source_id_ilike_relation(
                    selected_workspace_id, "%role%"
                )
            )
            target_user_profile_ids = [
                relation.target_id for relation in relation_response
            ]
            return self.repo.get_items_by_ids(target_user_profile_ids)

        child_relations = self.relation_repo.get_relations_by_source_id_and_relation(
            selected_workspace_id, RelationType.CHILD
        )
        children_ids = [relation.target_id for relation in child_relations]

        return self.repo.get_items_by_ids_and_item_type(
            children_ids, selected_item_type
        )

    def search_items(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_type: ItemType,
        search_text: str,
    ) -> List[ItemSchema]:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_items_permission = role_service.has_read_items_permission(item_type)

        if not has_read_items_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have the permission to view {item_type}s in this workspace.",
            )

        return self.repo.get_items_by_item_type_and_title_ilike(item_type, search_text)

    def fetch_items_by_ids(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_ids: List[str],
    ) -> List[ItemSchema]:
        # check if user has read items permission in the selected workspace
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_items_permission = role_service.has_read_all_items_permission()

        if not has_read_items_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have the permission to view items in this workspace.",
            )

        # children_items = (
        #     self.relation_repo.get_relations_by_source_id_target_ids_relation(
        #         selected_workspace_id, item_ids, RelationType.CHILD
        #     )
        # )

        # is_all_items_present_in_workspace = len(children_items) == len(item_ids)

        # if not is_all_items_present_in_workspace:
        #     raise HTTPException(
        #         status_code=404, detail="Items not found in the selected workspace."
        #     )

        return self.repo.get_items_by_ids(item_ids)

    async def update_full_item_metadata(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item: ItemSchema,
    ) -> ItemSchema:
        item_id = item.id
        item_type = item.item_type

        # check if user has edit full metadata permission in the selected workspace
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_edit_full_metadata_permission = role_service.has_update_item_permission(
            item_type
        )

        if not has_edit_full_metadata_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have the permission to edit items in this workspace.",
            )

        old_item = self.repo.get_item_by_id(item_id)
        old_item_image = old_item.image

        updated_item = self.repo.update_full_item(item)

        if not updated_item:
            raise HTTPException(status_code=400, detail="Invalid item id.")

        self._insert_tags(item.tags)

        if old_item_image:
            image_key = old_item_image.split("/")[-1]
            self.s3_client.delete_object(f"item-images/{image_key}")

        return updated_item

    def update_item_metadata(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
        item_type: str,
        field_name: str,
        field_value: Any,
    ) -> ItemSchema:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_edit_metadata_permission = role_service.has_update_item_field_permission(
            item_type, field_name
        )

        if not has_edit_metadata_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have the permission to edit items in this workspace.",
            )

        item = self.repo.get_item_by_id(item_id)
        old_item_image = item.image

        updated_item = self.repo.update_item_by_id_and_item_type(
            item_id, item_type, field_name, field_value
        )

        if not updated_item:
            raise HTTPException(status_code=400, detail="Invalid item id.")

        # create_edit_item_activity(loggedin_user_id, item, field_name, field_value)

        if field_name == "tags":
            if not isinstance(field_value, list):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid arguments: expected an array of tags.",
                )
            self._insert_tags(field_value)

        if field_name == "image":
            if old_item_image:
                image_key = old_item_image
                self.s3_client.delete_object(image_key)
                # image_key = old_item_image.split("/")[-1]
                # self.s3_client.delete_object(f"item-images/{image_key}")

        return updated_item

    def _is_file_deletable(self, item_id: str) -> bool:
        file_traceability = self._fetch_file_traceability(item_id)
        traceability_data = file_traceability.traceability_data
        projects = traceability_data.projects
        return False if len(projects) > 0 else True

    def _is_project_deletabe(self, item_id: str) -> bool:
        file_traceability = self._fetch_project_traceability(item_id)
        traceability_data = file_traceability.traceability_data
        reports = traceability_data.reports
        return False if len(reports) > 0 else True

    def _is_report_deletable(self, item_id: str) -> bool:
        file_traceability = self._fetch_report_traceability(item_id)
        traceability_data = file_traceability.traceability_data
        projects = traceability_data.projects
        return False if len(projects) > 0 else True

    def _is_workspace_deletable(self, item_id: str, loggedin_user_id: str) -> bool:
        relations = self.relation_repo.get_relations_by_source_id(item_id)
        are_items_in_workspace = False
        for relation in relations:
            if relation.target_id != loggedin_user_id:
                are_items_in_workspace = True

        return False if are_items_in_workspace else True

    def _is_role_deletable(self, item_id: str) -> bool:
        relations = self.relation_repo.get_relations_by_relation(f"role.{item_id}")
        return False if len(relations) > 0 else True

    def _is_item_deletable(
        self, item_id: str, loggedin_user_id: str, item_type: ItemType
    ) -> bool:
        if item_type == ItemType.FILE:
            return self._is_file_deletable(item_id)
        elif item_type == ItemType.PROJECT:
            return self._is_project_deletabe(item_id)
        elif item_type == ItemType.REPORT:
            return self._is_report_deletable(item_id)
        elif item_type == ItemType.WORKSPACE:
            return self._is_workspace_deletable(item_id, loggedin_user_id)
        elif item_type == ItemType.ROLE:
            return self._is_role_deletable(item_id)
        else:
            return False

    def delete_item(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
        item_type: str,
    ) -> ItemSchema:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_delete_item_permission = role_service.has_delete_item_permission(item_type)

        if not has_delete_item_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have the permission to delete {item_type}s in this workspace.",
            )

        can_delete = self._is_item_deletable(item_id, loggedin_user_id, item_type)

        if not can_delete:
            raise HTTPException(
                status_code=403,
                detail=f"This item cannot be deleted.",
            )

        current_time = get_current_time()

        updated_item = self.repo.update_item_by_id_and_item_type(
            item_id, item_type, "deleted_at", current_time
        )

        if not updated_item:
            raise HTTPException(status_code=400, detail="Invalid item id.")

        return updated_item

    def insert_item(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        new_item: NewItemSchema,
    ) -> ItemSchema:
        item_type = new_item.item_type
        items = self.repo.insert_items([new_item])
        item = items[0]
        item_id = item.id
        # item_title = item.title
        item_type = item.item_type
        item_tags = item.tags
        self._insert_tags(item_tags or [])

        # create_new_item_activity(
        #     loggedin_user_id,
        #     item_id,
        #     item_title,
        #     item_type,
        # )

        # Each new added item should first be added to the personal workspace of the user.
        # So, If selected_workspace_id is not the personal workspace of loggedin user
        # then find personal workspace id of loggedin user and then add the item to personal workspace of user
        personal_workspace_item = self.repo.get_item_by_system_key("personal_workspace")
        personal_workspace_item_id = personal_workspace_item.id

        all_personal_workspace_items = (
            self.relation_repo.get_relations_by_source_id_and_relation(
                personal_workspace_item_id, RelationType.CHILD
            )
        )
        all_personal_workspace_items_ids = [
            item.target_id for item in all_personal_workspace_items
        ]

        personal_workspace_of_loggedin_user_response = (
            self.relation_repo.get_relations_by_source_ids_and_target_id(
                all_personal_workspace_items_ids, loggedin_user_id
            )
        )
        personal_workspace_id_of_loggedin_user = (
            personal_workspace_of_loggedin_user_response[0].source_id
        )

        if personal_workspace_id_of_loggedin_user == selected_workspace_id:
            # if selected workspace is the personal workspace,
            # then simply add item to personal workspace
            rel = RelationSchema(
                source_id=personal_workspace_id_of_loggedin_user,
                target_id=item_id,
                relation=RelationType.CHILD,
            )
            self.relation_repo.insert_relations([rel])
        else:
            # if selected workspace is not the personal workspace,
            # then add item to both, the personal workspace and selected workspace
            rel1 = RelationSchema(
                source_id=personal_workspace_id_of_loggedin_user,
                target_id=item_id,
                relation=RelationType.CHILD,
            )
            rel2 = RelationSchema(
                source_id=selected_workspace_id,
                target_id=item_id,
                relation=RelationType.CHILD,
            )
            self.relation_repo.insert_relations([rel1, rel2])

        if item_type == ItemType.WORKSPACE:
            # if the new item is of type "workspace", then we also need to add the user to
            # the new workspace and assign "workspace_admin_role".
            role_item = self.repo.get_item_by_system_key("workspace_admin_role")
            role_id = role_item.id
            new_relation = RelationSchema(
                source_id=item_id,
                target_id=str(loggedin_user_id),
                relation=f"role.{role_id}",
            )
            self.relation_repo.insert_relations([new_relation])

        return item
