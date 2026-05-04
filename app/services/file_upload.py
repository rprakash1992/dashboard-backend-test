from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, List, Optional
from uuid import uuid4
import copy
import time
import math

# import core
from app.core.config import get_settings

# import models
from app.models.file_upload import UploadItemsDetails

# import schemas
from app.schemas.item import ItemSchema, NewItemSchema
from app.schemas.file import FileSchema
from app.schemas.file_upload import (
    UpdateFilePartsStatusResponseSchema,
    UpdateFilePartUrlsResponseSchema,
    UploadItemSchema,
    ResponseStatus,
    Checksum,
    FileSchema,
)

# import services
from app.services.s3_client import S3ClientService


settings = get_settings()

S3_MB = 1024 * 1024
MAX_SIZE_MB = 100
aws_s3_bucket = settings.aws_s3_bucket
aws_access_key = settings.aws_access_key
aws_secret_key = settings.aws_secret_key
aws_region = settings.aws_region


class ParentData(BaseModel):
    parent: Optional[int] = None
    isFolder: bool


class InitiateFileUploadResponse(BaseModel):
    file: FileSchema
    checksum: Checksum


class ExtractZipResponse(BaseModel):
    file: FileSchema
    item: ItemSchema


class ItemsAndParentsDataResponse(BaseModel):
    items_data: List[NewItemSchema]
    parents_data: List[ParentData]


class FilePathsAndUrlsResponse(BaseModel):
    file_paths: List[str]
    file_urls: List[str]


class FileUploadService:
    def __init__(self):
        self.s3_client = S3ClientService()

    def _generate_presigned_url(self, key: str, uploadId: str, partNumber: int):
        return self.s3_client.generate_presigned_url_for_put_object(
            key, uploadId, partNumber
        )

    def _complete_multipart_upload_s3(
        self, key: str, uploadId: str, partsToCommit: List
    ):
        self.s3_client.complete_multipart_upload_s3(key, uploadId, partsToCommit)

    def _get_expiry(self, url: str) -> int:
        # Find the last occurrence of '=' in the URL
        index_of_last_equals = url.rfind("=")

        # Get the substring after the last '=' (if '=' is found)
        expiry = url[index_of_last_equals + 1 :] if index_of_last_equals != -1 else None

        return int(expiry)

    def _create_multipart_upload(self, file_name: str):
        return self.s3_client.create_multipart_upload(file_name)

    def _get_upload_item_from_details(
        self, file_name: str, file_size: int, file_last_modified: int, db: Session
    ) -> UploadItemSchema:
        db_item = (
            db.query(UploadItemsDetails)
            .filter(
                UploadItemsDetails.file_name == file_name,
                UploadItemsDetails.file_size == file_size,
                UploadItemsDetails.file_last_modified == file_last_modified,
            )
            .first()
        )

        if db_item is None:
            return None

        else:
            return UploadItemSchema(
                id=db_item.id,
                file_name=db_item.file_name,
                file_size=db_item.file_size,
                file_last_modified=db_item.file_last_modified,
                s3=db_item.get_s3(),
                checksum=db_item.get_checksum(),
                parts=db_item.get_parts(),
            )

    def _set_upload_item(self, data: UploadItemSchema, db: Session):
        id = data.id
        file_name = data.file_name
        file_size = data.file_size
        file_last_modified = data.file_last_modified
        s3 = data.s3
        checksum = data.checksum.model_dump()
        parts = data.parts

        db_item = (
            db.query(UploadItemsDetails).filter(UploadItemsDetails.id == id).first()
        )

        if db_item is None:
            item = UploadItemsDetails()
            item.id = id
            item.file_name = file_name
            item.file_size = file_size
            item.file_last_modified = file_last_modified
            item.set_s3(s3)
            item.set_checksum(checksum)
            item.set_parts(parts)
            db.add(item)
            db.commit()
            db.refresh(item)

        else:
            db_item.id = id
            db_item.file_name = file_name
            db_item.file_size = file_size
            db_item.file_last_modified = file_last_modified
            db_item.set_s3(s3)
            db_item.set_checksum(checksum)
            db_item.set_parts(parts)
            db.commit()
            db.refresh(db_item)

    def _get_upload_item(self, id: str, db: Session) -> UploadItemSchema:
        db_item = (
            db.query(UploadItemsDetails).filter(UploadItemsDetails.id == id).first()
        )

        if db_item is None:
            return None

        else:
            return UploadItemSchema(
                id=db_item.id,
                file_name=db_item.file_name,
                file_size=db_item.file_size,
                file_last_modified=db_item.file_last_modified,
                s3=db_item.get_s3(),
                checksum=db_item.get_checksum(),
                parts=db_item.get_parts(),
            )

    def _delete_upload_item(self, id: str, db: Session):
        db_item = (
            db.query(UploadItemsDetails).filter(UploadItemsDetails.id == id).first()
        )

        db.delete(db_item)
        db.commit()

    def _update_upload_item(self, id: str, parts: List[Any], db: Session):
        db_item = (
            db.query(UploadItemsDetails).filter(UploadItemsDetails.id == id).first()
        )

        if db_item is None:
            return None

        else:
            db_item.set_parts(parts)
            db.commit()
            db.refresh(db_item)

    def _get_new_parts_data(self, file_data: UploadItemSchema, db: Session):
        file_size = file_data.file_size
        part_size = 5 * 1024 * 1024
        total_chunks = math.ceil(file_size / part_size)
        parts = []
        pos = 0
        len = part_size

        lastChunkSize = file_size % part_size
        endLoop = False

        for index in range(1, total_chunks + 1):
            # during last iteration, if (pos + part_size) becomes greater than the file size, then
            if pos + part_size > file_size:
                len = (
                    file_size - pos + 1
                )  # set the len equal to the length of remaining chunk size

            # if the len for the last chunk could be less that 1MB
            if index == total_chunks - 1 and lastChunkSize < (1024 * 1024):
                # then add the last chunk into the second last chunk
                len = len + lastChunkSize
                # and end the loop in second last iteration using endLoop flag
                endLoop = True

            new_part = {
                "id": index,
                "pos": pos,
                "length": len,
                "checksum": None,
                "status": "upload_pending",
            }
            pos = pos + part_size
            parts.append(new_part)

            if endLoop:
                break

        file_data.parts = parts
        self._set_upload_item(file_data, db)

        part_info_to_return = []

        for idx, part_info in enumerate(parts):
            key = file_data.s3["Key"]
            uploadId = file_data.s3["UploadId"]
            partNumber = idx + 1
            presigned_url = self._generate_presigned_url(key, uploadId, partNumber)

            url_data = {"url": presigned_url}

            new_part_info_to_return = copy.deepcopy(part_info)
            new_part_info_to_return["upload"] = url_data
            part_info_to_return.append(new_part_info_to_return)
            part_info["s3"] = url_data

        file_data.parts = parts
        self._set_upload_item(file_data, db)

        return part_info_to_return

    async def initiate_file_upload(
        self,
        file_s3_url: str,
        file_name: str,
        file_size: int,
        file_last_modified: int,
        db: Session,
    ) -> InitiateFileUploadResponse:
        upload_item = self._get_upload_item_from_details(
            file_name, file_size, file_last_modified, db
        )

        if upload_item:
            # if a prevous upload fails and user retries to upload the same file
            # then the upload_item will not be None
            file = FileSchema(
                id=upload_item.id,
                name=upload_item.file_name,
                size=upload_item.file_size,
                lastModified=upload_item.file_last_modified,
            )
            return InitiateFileUploadResponse(file=file, checksum=upload_item.checksum)

        else:
            checksum = Checksum(method="sha256")
            s3 = {}
            parts = []
            unique_id = str(uuid4())

            upload_item = UploadItemSchema(
                id=unique_id,
                file_name=file_name,
                file_size=file_size,
                file_last_modified=file_last_modified,
                s3=s3,
                checksum=checksum,
                parts=parts,
            )

            self._set_upload_item(upload_item, db)

            create_multipart_upload_response = self._create_multipart_upload(
                file_s3_url
            )

            upload_item.s3 = create_multipart_upload_response

            self._set_upload_item(upload_item, db)

            file = FileSchema(
                id=unique_id,
                name=file_name,
                size=file_size,
                lastModified=file_last_modified,
            )

            return InitiateFileUploadResponse(file=file, checksum=checksum)

    async def update_file_part_urls(
        self, file_id: str, db: Session
    ) -> UpdateFilePartUrlsResponseSchema:
        upload_item = self._get_upload_item(file_id, db)

        file_data = upload_item
        old_parts_data = file_data.parts
        parts_info_to_return = []

        if old_parts_data and len(old_parts_data) > 0:
            for idx, part_info in enumerate(old_parts_data):
                new_part_info_to_return = copy.deepcopy(part_info)
                del new_part_info_to_return["s3"]

                part_s3 = part_info["s3"]
                url = part_s3["url"]
                expiry = self._get_expiry(url)
                current_time = time.time()
                status = part_info["status"]

                if current_time < expiry or status == "upload_verified":
                    new_part_info_to_return["upload"] = part_s3

                else:
                    key = file_data.s3["Key"]
                    uploadId = file_data.s3["UploadId"]
                    partNumber = part_info["id"]
                    presigned_url = self._generate_presigned_url(
                        key, uploadId, partNumber
                    )
                    part_s3["url"] = presigned_url
                    part_info["s3"] = part_s3
                    new_part_info_to_return["upload"] = part_s3

                parts_info_to_return.append(new_part_info_to_return)

            response_status = ResponseStatus(success=True, errorMessage="")
            return UpdateFilePartUrlsResponseSchema(
                parts=parts_info_to_return, status=response_status
            )

        else:
            new_parts_data = self._get_new_parts_data(file_data, db)
            response_status = ResponseStatus(success=True, errorMessage="")
            return UpdateFilePartUrlsResponseSchema(
                parts=new_parts_data, status=response_status
            )

    async def update_file_parts_status(
        self,
        file_id: str,
        parts: List[Any],
        est_time: int,
        # web_socket_repository: WebSocketRepository,
        db: Session,
    ) -> UpdateFilePartsStatusResponseSchema:
        upload_item = self._get_upload_item(file_id, db)
        old_parts = []
        upload_item_s3 = upload_item.s3
        upload_id = upload_item_s3["UploadId"]
        key = upload_item_s3["Key"]
        old_parts = upload_item.parts

        for idx, part_info in enumerate(old_parts):
            part_id = part_info["id"]

            item = next((item for item in parts if item["id"] == part_id), None)
            checksum = item["checksum"]
            status = item["status"]

            if status == "upload_performed":
                etag = item["upload"]["response"]["etag"]
                if checksum == etag[1:-1]:
                    url = item["upload"]["url"]
                    response = item["upload"]["response"]

                    item["status"] = "upload_verified"
                    item["upload"] = {
                        "url": url,
                        "response": response,
                        "success": True,
                        "errorMessage": "",
                    }

                    part_info["status"] = "upload_verified"
                    part_info["s3"] = {
                        "url": url,
                        "response": response,
                        "success": True,
                        "errorMessage": "",
                    }

        upload_item.parts = old_parts
        self._update_upload_item(upload_item.id, upload_item.parts, db)

        # verified_parts = [
        #     item for item in parts if item["status"] == "upload_verified"]
        # await web_socket_repository.broadcast_message(file_id, {"estimated_time": est_time, "total_parts": len(parts), "uploaded_parts": len(verified_parts)})

        all_verified = all(item["status"] == "upload_verified" for item in parts)

        if all_verified:
            parts_to_commit = []

            for d in parts:
                one_part = {
                    "ETag": d["upload"]["response"]["etag"],
                    "PartNumber": d["id"],
                }
                parts_to_commit.append(one_part)

            self._complete_multipart_upload_s3(key, upload_id, parts_to_commit)

            delete_upload_item_resp = self._delete_upload_item(file_id, db)
            # await web_socket_repository.broadcast_message(file_id, {"estimated_time": 0, "total_parts": len(parts), "uploaded_parts": len(parts)})
            response_status = ResponseStatus(success=True, errorMessage="")
            return UpdateFilePartsStatusResponseSchema(
                status=response_status, parts=parts, upload_complete=True
            )

        else:
            response_status = ResponseStatus(success=True, errorMessage="")
            return UpdateFilePartsStatusResponseSchema(
                status=response_status, parts=parts, upload_complete=False
            )

    # async def _insert_job_item_while_extract(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     item_title: str,
    #     item_id: str,
    #     first_item_id: str,
    # ):
    #     insert_job_response = self.job_service.insert_job(
    #         selected_workspace_id=selected_workspace_id,
    #         loggedin_user_id=loggedin_user_id,
    #         title=item_title,
    #         description="",
    #         image="",
    #         tags=[],
    #         job_type=JobType.ZIP_TO_FOLDER,
    #         total_steps="5",
    #         completed_steps="0",
    #     )
    #     added_item = insert_job_response.item
    #     new_item_id = added_item.id

    #     # add relation between the zip item which was extracted and the job item
    #     zip_job_relation = RelationSchema(
    #         source_id=item_id, target_id=new_item_id, relation=RelationType.JOB
    #     )
    #     # add relation between the job and the folder item created by extracting zip
    #     job_folder_relation = RelationSchema(
    #         source_id=new_item_id,
    #         target_id=first_item_id,
    #         relation=RelationType.JOB_OUTPUT,
    #     )

    #     self.relation_service.insert_relation(zip_job_relation)
    #     self.relation_service.insert_relation(job_folder_relation)
    #     return new_item_id

    # async def _prepare_extraction(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     item_id: str,
    # ):
    #     # get item metadata of the file to be extracted
    #     items_response = self.item_service.fetch_items_by_ids(
    #         selected_workspace_id, loggedin_user_id, [item_id]
    #     )
    #     item = items_response[0]

    #     item_title = item.title
    #     # if item title has .zip or any other extension then remove it from the end
    #     if item_title.find(".") > 0:
    #         item_title = item_title[0 : item_title.rfind(".")]

    #     insert_file_response = self.file_service.insert_file(
    #         selected_workspace_id=selected_workspace_id,
    #         loggedin_user_id=loggedin_user_id,
    #         title=item_title,
    #         description="",
    #         image="",
    #         tags=[],
    #         file_extension="vcollab_folder",
    #         is_uploaded=False,
    #         parent=None,
    #         url="",
    #     )
    #     output_item = insert_file_response.item
    #     output_file = insert_file_response.file

    #     job_item_id = await self._insert_job_item_while_extract(
    #         selected_workspace_id,
    #         loggedin_user_id,
    #         item_title,
    #         item_id,
    #         str(output_item.id),
    #     )

    #     return {
    #         "output_item": output_item,
    #         "output_file": output_file,
    #         "job_item_id": job_item_id,
    #     }

    # async def extract_zip_prefect(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     item_id: str,
    # ):
    #     # Create initial folder item (synchronous part)
    #     result = await self._prepare_extraction(
    #         selected_workspace_id, loggedin_user_id, item_id
    #     )

    #     output_file = result.get("output_file")
    #     output_item = result.get("output_item")
    #     output_item_id = output_item.id
    #     job_item_id = result.get("job_item_id")

    #     deployment = await self.prefect_client_service.read_deployment_by_name(
    #         "extract-zip-workflow/extract-zip-deployment"
    #     )

    #     # Trigger Prefect workflow (asynchronous part)
    #     flow_run = await self.prefect_client_service.trigger_extract_zip_flow(
    #         deployment.id,
    #         loggedin_user_id=loggedin_user_id,
    #         selected_workspace_id=selected_workspace_id,
    #         input_item_id=item_id,
    #         output_item_id=output_item_id,
    #     )

    #     if flow_run.id:
    #         self.job_service.update_job_field_by_id(
    #             selected_workspace_id,
    #             loggedin_user_id,
    #             str(job_item_id),
    #             "run_id",
    #             str(flow_run.id),
    #         )

    #         return {
    #             "file": output_file,
    #             "item": output_item,
    #         }

    # async def _prepare_compression(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     item_id: str,
    # ):
    #     items_response = self.item_service.fetch_items_by_ids(
    #         selected_workspace_id,
    #         loggedin_user_id,
    #         [item_id],
    #     )
    #     item = items_response[0]

    #     item_title = item.title
    #     # If the title already ends with ".zip" then keep the same title
    #     # else add ".zip" at the end
    #     new_item_title = (
    #         item_title if item_title.endswith(".zip") else f"{item_title}.zip"
    #     )

    #     # If we are zipping a folder which is inside another folder
    #     # then we need to zip the folder in the same directory
    #     # So we need to set the parent field pointing to the id of parent folder item while inserting new file below
    #     files_response = self.file_service.fetch_files_by_ids(
    #         selected_workspace_id,
    #         loggedin_user_id,
    #         [item_id],
    #     )
    #     file = files_response[0]

    #     insert_file_response = self.file_service.insert_file(
    #         selected_workspace_id=selected_workspace_id,
    #         loggedin_user_id=loggedin_user_id,
    #         title=new_item_title,
    #         description="",
    #         image="",
    #         tags=[],
    #         file_extension="zip",
    #         is_uploaded=False,
    #         parent=file.parent,
    #         url=f"{str(uuid4())}.zip",
    #     )
    #     file = insert_file_response.file
    #     new_item = insert_file_response.item
    #     # new_item_id = new_item.id

    #     return {
    #         "output_file": file,
    #         "output_item": new_item,
    #     }

    # async def _finalize_compression(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     item_id: str,
    #     new_item_title: str,
    #     new_item_id: str,
    #     flow_run_id: str,
    # ):
    #     insert_job_response = self.job_service.insert_job(
    #         selected_workspace_id=selected_workspace_id,
    #         loggedin_user_id=loggedin_user_id,
    #         title=new_item_title,
    #         description="",
    #         image="",
    #         tags=[],
    #         job_type=JobType.FOLDER_TO_ZIP,
    #         run_id=flow_run_id,
    #         total_steps="5",
    #         completed_steps="0",
    #     )
    #     added_item = insert_job_response.item
    #     added_item_id = added_item.id

    #     # add relation between the folder item which was compressed and the job item
    #     zip_job_relation = RelationSchema(
    #         source_id=item_id, target_id=str(added_item_id), relation=RelationType.JOB
    #     )
    #     # add relation between the job and the zip item created by compressing folder
    #     job_folder_relation = RelationSchema(
    #         source_id=str(added_item_id),
    #         target_id=new_item_id,
    #         relation=RelationType.JOB_OUTPUT,
    #     )

    #     self.relation_service.insert_relation(zip_job_relation)
    #     self.relation_service.insert_relation(job_folder_relation)

    # async def compress_file_prefect(
    #     self,
    #     selected_workspace_id: str,
    #     loggedin_user_id: str,
    #     item_id: str,
    # ):
    #     response = await self._prepare_compression(
    #         selected_workspace_id, loggedin_user_id, item_id
    #     )
    #     output_file = response.get("output_file")
    #     output_item = response.get("output_item")
    #     output_item_id = output_item.id
    #     output_item_title = output_item.title

    #     deployment = await self.prefect_client_service.read_deployment_by_name(
    #         "compress-file-workflow/compress-file-deployment"
    #     )

    #     # run the whole file compression task in background
    #     flow_run = await self.prefect_client_service.trigger_compress_file_flow(
    #         deployment.id,
    #         selected_workspace_id=selected_workspace_id,
    #         loggedin_user_id=loggedin_user_id,
    #         input_item_id=item_id,
    #         output_item_id=output_item_id,
    #     )

    #     if flow_run.id:
    #         await self._finalize_compression(
    #             selected_workspace_id,
    #             loggedin_user_id,
    #             item_id,
    #             output_item_title,
    #             str(output_item_id),
    #             str(flow_run.id),
    #         )

    #     # return newly added file and item_metadata to frontend
    #     return {"file": output_file, "item": output_item}
    #     # return ExtractZipResponse(file=file, item=new_item)
