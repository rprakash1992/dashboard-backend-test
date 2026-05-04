from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from uuid import uuid4

# import repositories
from app.repositories.database_dashboard.item import ItemRepository
from app.repositories.database_dashboard.relation import RelationRepository
from app.repositories.database_dashboard.file import FileRepository

# import schemas
from app.schemas.file import FileSchema, InsertFileResponse
from app.schemas.item import ItemType, NewItemSchema
from app.schemas.relation import RelationSchema, RelationType
from app.schemas.job import JobType

# import services
from app.services.role import RoleService
from app.services.item import ItemService
from app.services.s3_client import S3ClientService
from app.services.argo_client import ArgoClientService
from app.services.job import JobService
from app.services.relation import RelationService


class FileService:
    def __init__(
        self,
        db: Session,
        # prefect_db: Session
    ):
        self.db = db
        self.repo = FileRepository(db)
        self.item_repo = ItemRepository(db)
        self.relation_repo = RelationRepository(db)
        self.relation_service = RelationService(db)
        self.item_service = ItemService(db)
        self.job_service = JobService(db)
        self.s3_client = S3ClientService()
        self.argo_client_service = ArgoClientService()

    def insert_file(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        title: str,
        description: str,
        image: str,
        tags: List[str],
        file_extension: str,
        is_uploaded: Optional[bool] = False,
        parent: Optional[str] = None,
        url: Optional[str] = None,
    ) -> InsertFileResponse:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_create_permission = role_service.has_create_item_permission(ItemType.FILE)

        if not has_create_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to create file."
            )

        item = NewItemSchema(
            title=title,
            item_type=ItemType.FILE,
            description=description,
            image=image,
            tags=tags,
        )
        new_item_response = self.item_service.insert_item(
            selected_workspace_id, loggedin_user_id, item
        )
        new_item_id = new_item_response.id

        new_file = FileSchema(
            id=new_item_id,
            url=url if url else f"{new_item_id}.{file_extension}",
            mime_type=file_extension,
            is_uploaded=is_uploaded,
            parent=parent,
        )
        new_file_response = self.repo.insert_files([new_file])
        return InsertFileResponse(item=new_item_response, file=new_file_response[0])

    # def insert_files(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     files_data: List[FileSchema],
    # ) -> List[FileSchema]:
    #     """
    #     Inserts files to the "files" table.

    #     Args:
    #         selected_workspace_id (str): id of workspace selected by user
    #         loggedin_user_id (str): id of logged in user
    #         files_data (List[FileSchema]): list of new files to be inserted
    #     Returns:
    #         Returns the list of newly inserted files
    #     """
    #     role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
    #     has_create_permission = role_service.has_create_item_permission(ItemType.FILE)

    #     if not has_create_permission:
    #         raise HTTPException(
    #             status_code=403, detail="Unauthorized: Not permitted to create file."
    #         )
    #     return self.repo.insert_files(files_data)

    def fetch_files_by_ids(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        file_ids: List[str],
    ) -> List[FileSchema]:
        """
        Fetches the files based on file id.

        Args:
            selected_workspace_id (str): id of workspace selected by user
            loggedin_user_id (str): id of logged in user
            file_ids (List[str]): list of file ids to be fetched
        Returns:
            Returns the list of fetched files
        """
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.FILE
        )

        # raise error if user does not have the permission
        if not has_read_contents_permission:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Not permitted to access file contents.",
            )

        # check if all the file ids exist in the selected workspace
        relations = self.relation_repo.get_relations_by_source_id_and_target_ids(
            selected_workspace_id, file_ids
        )

        if len(relations) != len(file_ids):
            raise HTTPException(
                status_code=404,
                detail="Not found: One or more files not found in selected workspace.",
            )

        # only if all the file_ids are found in selected_workspace_id, then fetch files and return
        return self.repo.get_files_by_ids(file_ids)

    def get_files_by_field_name_field_val(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        field_name: str,
        field_val: Any,
    ) -> List[FileSchema]:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.FILE
        )

        if not has_read_contents_permission:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Not permitted to access file content.",
            )

        return self.repo.get_files_by_field_and_name_field_val(field_name, field_val)

    def update_file_field_by_id(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        file_id: str,
        field_name: str,
        field_val: Any,
    ) -> FileSchema:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_update_contents_permission = role_service.has_update_content_permission(
            ItemType.FILE
        )

        if not has_update_contents_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to update file."
            )

        return self.repo.update_file_field_by_id(file_id, field_name, field_val)

    async def update_file_record(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        file: FileSchema,
    ) -> FileSchema | None:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_update_contents_permission = role_service.has_update_content_permission(
            ItemType.FILE
        )

        if not has_update_contents_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to update file."
            )

        return self.repo.update_file_record(file)

    def copy_item_to_another_folder(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
        item_id_to: str,
    ) -> bool:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_metadata_permission = role_service.has_read_metadata_permission(
            ItemType.FILE
        )
        has_read_contents_permission = role_service.has_read_content_permission(
            ItemType.FILE
        )
        has_create_item_permission = role_service.has_create_item_permission(
            ItemType.FILE
        )

        has_permission = (
            has_read_metadata_permission
            and has_read_contents_permission
            and has_create_item_permission
        )

        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Not authorized to perform this operation.",
            )

        items = self.item_repo.get_items_by_ids([item_id])

        if len(item) == 0:
            raise HTTPException(
                status_code=404,
                detail="Not found: Folder item to which copying is not found.",
            )
        item = items[0]

        file = self.repo.get_file_by_id(item_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail="Not found: Folder to which copying is not found.",
            )

        new_item = NewItemSchema(
            title=item.title,
            item_type=item.item_type,
            description=item.description,
            image=item.image,
            tags=item.tags,
        )
        insert_items_resp = self.item_repo.insert_items([new_item])
        new_item_id = insert_items_resp[0].id
        mime_type = file.mime_type

        new_file = FileSchema(
            id=new_item_id,
            url=file.url,
            downloader_type=file.downloader_type,
            downloader_args=file.downloader_args,
            cache_state=file.cache_state,
            local_cache_file_path=file.local_cache_file_path,
            mime_type=file.mime_type,
            is_uploaded=file.is_uploaded,
            parent=item_id_to,
        )
        self.repo.insert_files([new_file])

        if mime_type == "vcollab_folder":
            files_resp = self.repo.get_files_by_field_and_name_field_val(
                "parent", item_id
            )

            if len(files_resp) > 0:
                for f in files_resp:
                    self.copy_item_to_another_folder(
                        selected_workspace_id,
                        loggedin_user_id,
                        f.id,
                        new_item_id,
                    )

        return True

    def download_file(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        file_id: str,
    ) -> str:
        role_service = RoleService(selected_workspace_id, loggedin_user_id, self.db)
        has_read_content_permission = role_service.has_read_content_permission(
            ItemType.FILE
        )
        has_read_metadata_permission = role_service.has_read_metadata_permission(
            ItemType.FILE
        )

        has_download_permission = (
            has_read_content_permission and has_read_metadata_permission
        )

        if not has_download_permission:
            raise HTTPException(
                status_code=403, detail="Unauthorized: Not permitted to download file."
            )

        item = self.item_repo.get_item_by_id(file_id)
        file = self.repo.get_file_by_id(file_id)
        item_title = item.title
        url = file.url

        download_url = self.s3_client.generate_presigned_url_for_get_object(
            url, item_title
        )

        # create_download_activity(loggedin_user_id, file_id, "file", db)
        return download_url

    async def _insert_job_item_while_extract(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_title: str,
        item_id: str,
        first_item_id: str,
    ):
        insert_job_response = self.job_service.insert_job(
            selected_workspace_id=selected_workspace_id,
            loggedin_user_id=loggedin_user_id,
            title=item_title,
            description="",
            image="",
            tags=[],
            job_type=JobType.ZIP_TO_FOLDER,
            total_steps=7,
            completed_steps=0,
        )
        added_item = insert_job_response.item
        new_item_id = added_item.id

        # add relation between the zip item which was extracted and the job item
        zip_job_relation = RelationSchema(
            source_id=item_id, target_id=new_item_id, relation=RelationType.JOB
        )
        # add relation between the job and the folder item created by extracting zip
        job_folder_relation = RelationSchema(
            source_id=new_item_id,
            target_id=first_item_id,
            relation=RelationType.JOB_OUTPUT,
        )

        self.relation_service.insert_relation(zip_job_relation)
        self.relation_service.insert_relation(job_folder_relation)
        return new_item_id

    async def _prepare_extraction(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
    ):
        # get item metadata of the file to be extracted
        items_response = self.item_service.fetch_items_by_ids(
            selected_workspace_id, loggedin_user_id, [item_id]
        )
        item = items_response[0]

        item_title = item.title
        # if item title has .zip or any other extension then remove it from the end
        if item_title.find(".") > 0:
            item_title = item_title[0 : item_title.rfind(".")]

        insert_file_response = self.insert_file(
            selected_workspace_id=selected_workspace_id,
            loggedin_user_id=loggedin_user_id,
            title=item_title,
            description="",
            image="",
            tags=[],
            file_extension="vcollab_folder",
            is_uploaded=False,
            parent=None,
            url="",
        )
        output_item = insert_file_response.item
        output_file = insert_file_response.file

        job_item_id = await self._insert_job_item_while_extract(
            selected_workspace_id,
            loggedin_user_id,
            item_title,
            item_id,
            str(output_item.id),
        )

        return {
            "output_item": output_item,
            "output_file": output_file,
            "job_item_id": job_item_id,
        }

    async def extract_zip_prefect(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
    ):
        # Create initial folder item (synchronous part)
        result = await self._prepare_extraction(
            selected_workspace_id, loggedin_user_id, item_id
        )

        output_file = result.get("output_file")
        output_item = result.get("output_item")
        output_item_id = output_item.id
        job_item_id = result.get("job_item_id")
        
        deployment_id = "extract-zip-workflow"
        
        # Trigger Prefect workflow (asynchronous part)
        flow_run = await self.argo_client_service.trigger_extract_zip_flow(
            deployment_id,
            loggedin_user_id=loggedin_user_id,
            selected_workspace_id=selected_workspace_id,
            input_item_id=item_id,
            output_item_id=output_item_id,
        )

        if flow_run.id:
            self.job_service.update_job_field_by_id(
                selected_workspace_id,
                loggedin_user_id,
                str(job_item_id),
                "run_id",
                str(flow_run.id),
            )

            return {
                "file": output_file,
                "item": output_item,
            }

    async def _prepare_compression(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
    ):
        items_response = self.item_service.fetch_items_by_ids(
            selected_workspace_id,
            loggedin_user_id,
            [item_id],
        )
        item = items_response[0]

        item_title = item.title
        # If the title already ends with ".zip" then keep the same title
        # else add ".zip" at the end
        new_item_title = (
            item_title if item_title.endswith(".zip") else f"{item_title}.zip"
        )

        # If we are zipping a folder which is inside another folder
        # then we need to zip the folder in the same directory
        # So we need to set the parent field pointing to the id of parent folder item while inserting new file below
        files_response = self.fetch_files_by_ids(
            selected_workspace_id,
            loggedin_user_id,
            [item_id],
        )
        file = files_response[0]

        insert_file_response = self.insert_file(
            selected_workspace_id=selected_workspace_id,
            loggedin_user_id=loggedin_user_id,
            title=new_item_title,
            description="",
            image="",
            tags=[],
            file_extension="zip",
            is_uploaded=False,
            parent=file.parent,
            url=f"{str(uuid4())}.zip",
        )
        file = insert_file_response.file
        new_item = insert_file_response.item
        # new_item_id = new_item.id

        return {
            "output_file": file,
            "output_item": new_item,
        }

    async def _finalize_compression(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
        new_item_title: str,
        new_item_id: str,
        flow_run_id: str,
    ):
        insert_job_response = self.job_service.insert_job(
            selected_workspace_id=selected_workspace_id,
            loggedin_user_id=loggedin_user_id,
            title=new_item_title,
            description="",
            image="",
            tags=[],
            job_type=JobType.FOLDER_TO_ZIP,
            run_id=flow_run_id,
            total_steps=6,
            completed_steps=0,
        )
        added_item = insert_job_response.item
        added_item_id = added_item.id

        # add relation between the folder item which was compressed and the job item
        zip_job_relation = RelationSchema(
            source_id=item_id, target_id=str(added_item_id), relation=RelationType.JOB
        )
        # add relation between the job and the zip item created by compressing folder
        job_folder_relation = RelationSchema(
            source_id=str(added_item_id),
            target_id=new_item_id,
            relation=RelationType.JOB_OUTPUT,
        )

        self.relation_service.insert_relation(zip_job_relation)
        self.relation_service.insert_relation(job_folder_relation)

    async def compress_file_prefect(
        self,
        selected_workspace_id: str,
        loggedin_user_id: str,
        item_id: str,
    ):
        response = await self._prepare_compression(
            selected_workspace_id, loggedin_user_id, item_id
        )
        output_file = response.get("output_file")
        output_item = response.get("output_item")
        output_item_id = output_item.id
        output_item_title = output_item.title
        
        deployment_id = "compress-file-workflow"

        # run the whole file compression task in background
        flow_run = await self.argo_client_service.trigger_compress_file_flow(
            deployment_id,
            selected_workspace_id=selected_workspace_id,
            loggedin_user_id=loggedin_user_id,
            input_item_id=item_id,
            output_item_id=output_item_id,
        )

        if flow_run.id:
            await self._finalize_compression(
                selected_workspace_id,
                loggedin_user_id,
                item_id,
                output_item_title,
                str(output_item_id),
                str(flow_run.id),
            )

        # return newly added file and item_metadata to frontend
        return {"file": output_file, "item": output_item}
        # return ExtractZipResponse(file=file, item=new_item)
