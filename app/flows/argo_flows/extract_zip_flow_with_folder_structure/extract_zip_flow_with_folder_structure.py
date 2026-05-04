from typing import Any, List, Optional
from pydantic import BaseModel
from uuid import uuid4
import zipfile
import shutil
import os

# import core
from app.core.dashboard_database import get_dashboard_db
# from app.core.prefect_database import get_prefect_db
from app.core.config import get_settings

# import schemas
from app.schemas.item import NewItemSchema
from app.schemas.workflow import WorkflowSchema

# import services
from app.services.job import JobService
from app.services.workflow import WorkflowService
from app.services.file import FileService
from app.services.item import ItemService
from app.services.s3_client import S3ClientService


settings = get_settings()

work_dir = "./work_dir"


class ParentData(BaseModel):
    parent: Optional[int] = None
    isFolder: bool


class ItemsAndParentsDataResponse(BaseModel):
    items_data: List[NewItemSchema]
    parents_data: List[ParentData]


class PrepareExtractionResponse(BaseModel):
    file_download_path: str
    file_extraction_path: str
    item_title: str
    file_s3_key: str
    
    
class UpdateJobStepsProgress:
    def __init__(self, selected_workspace_id, loggedin_user_id, job_id):
        self.selected_workspace_id = selected_workspace_id
        self.loggedin_user_id = loggedin_user_id
        self.job_id = job_id

    def update(self, completed_steps: int):
        db = next(get_dashboard_db())
        job_service = JobService(db)
        job_service.update_job_field_by_id(
            self.selected_workspace_id,
            self.loggedin_user_id,
            self.job_id,
            "completed_steps",
            completed_steps,
        )


async def download_file_from_s3(
    file_s3_key: str,
    download_path: str,
) -> None:
    """Download file from S3 with automatic retries."""
    # Create local download path directory if it doesn't exist
    s3_client = S3ClientService()
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    s3_client.download_file_to_local_path(file_s3_key, download_path)


def extract_zip_file(zip_path: str, extract_to: str) -> list[str]:
    """Extract zip file and return list of extracted files."""
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
        file_list = zip_ref.namelist()
    return file_list


def upload_files_to_s3(file_paths: list[str], file_urls: list[str]) -> None:
    """Upload extracted files back to S3."""
    s3_client = S3ClientService()
    for file_path, s3_key in zip(file_paths, file_urls):
        if file_path.endswith("/") or not s3_key:
            continue
        s3_client.upload_local_file(file_path, s3_key)


async def build_file_paths_and_urls(
    loggedin_user_id: str,
    selected_workspace_id: str,
    item_title: str,
    output_item_id: Any,
    file_list_extracted: list[str],
    extraction_path: str,
):
    db = next(get_dashboard_db())

    # Your database update logic here
    # Add items and files to database
    # file_list is the list of file inside the zip
    # for e.g ["folder1/", "folder1/file.txt", "folder1/file2.txt", "folder1/folder2/", "folder1/folder2/file3.txt"]
    file_list = [f"{item_title}/"]
    for item in file_list_extracted:
        file_list.append(f"{item_title}/{item}")

    # get s3_key of the output_item_id from workflows table
    workflow_service = WorkflowService(db)
    workflows_response = workflow_service.fetch_workflows_by_ids(
        selected_workspace_id, loggedin_user_id, [output_item_id]
    )
    workflow = workflows_response[0]
    s3_key_of_flow = workflow.s3_key
    # uniquely generated s3 keys for the files to be uploaded
    file_urls = []
    for file_list_item in file_list:
        url = (
            ""
            if file_list_item.endswith("/")
            else f"{s3_key_of_flow}/{file_list_item[file_list_item.find('/') + 1:]}"
        )
        file_urls.append(url)

    # paths to local extracted files which have to be uploaded back to s3 bucket
    # file_list entries are like "item_title/subdir/file.py"
    # the zip is extracted directly into extraction_path (no item_title subfolder on disk),
    # so strip the leading "item_title/" prefix to get the actual local path
    file_paths = [
        f"{extraction_path}/{item[item.find('/') + 1:]}" for item in file_list
    ]

    return {
        "file_paths": file_paths,
        "file_urls": file_urls,
    }


def cleanup_temp_files(path: str):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


async def prepare_extraction(
    loggedin_user_id: str,
    selected_workspace_id: str,
    input_item_id: str,
):
    db = next(get_dashboard_db())
    # prefect_db = next(get_prefect_db())

    file_service = FileService(
        db,
        # prefect_db
    )
    files = file_service.fetch_files_by_ids(
        selected_workspace_id, loggedin_user_id, [input_item_id]
    )
    file = files[0]

    file_url = file.url
    file_s3_key = file_url
    unique_id = uuid4()
    # work_dir = "./work_dir"
    # create a unique folder inside "./workdir/"
    unique_folder_in_work_dir = f"{work_dir}/{unique_id}"
    # path where the file will be downloaded e.g. "./work_dir/some_unique_folder/file.zip"
    file_download_path = f"{unique_folder_in_work_dir}/{file_s3_key}"
    # path where the zip file will be extracted
    file_extraction_path = unique_folder_in_work_dir

    if file_s3_key:
        # get item metadata of the file to be extracted
        item_service = ItemService(db)
        items_response = item_service.fetch_items_by_ids(
            selected_workspace_id, loggedin_user_id, [input_item_id]
        )
        item = items_response[0]

        item_title = item.title
        # if item title has .zip or any other extension then remove it from the end
        if item_title.find(".") > 0:
            item_title = item_title[0 : item_title.rfind(".")]

        return PrepareExtractionResponse(
            file_download_path=file_download_path,
            file_extraction_path=file_extraction_path,
            item_title=item_title,
            file_s3_key=file_s3_key,
        )
    else:
        raise ValueError(
            "------->>>>>>file_s3_key not found at prepare_extraction step."
        )


async def update_workflow(
    selected_workspace_id: str, loggedin_user_id: str, output_item_id: str
):
    db = next(get_dashboard_db())

    workflow_service = WorkflowService(db)
    workflows_response = workflow_service.fetch_workflows_by_ids(
        selected_workspace_id, loggedin_user_id, [output_item_id]
    )
    workflow = workflows_response[0]

    updated_flow = WorkflowSchema(
        id=workflow.id,
        s3_key=workflow.s3_key,
        flow_function_name=workflow.flow_function_name,
        deployment_id=workflow.deployment_id,
        deployment_name=workflow.deployment_name,
        flow_id=workflow.flow_id,
        status="active",
        is_valid=True,
        parameter_schema=workflow.parameter_schema,
    )
    workflow_service.update_workflow(
        selected_workspace_id, loggedin_user_id, updated_flow
    )


# @task(name="update-upload-status")
# async def update_upload_status(
#     selected_workspace_id: str, loggedin_user_id: str, output_item_id: str
# ):
#     db = next(get_dashboard_db())
#     prefect_db = next(get_prefect_db())

#     file_service = FileService(db, prefect_db)
#     file_service.update_file_field_by_id(
#         selected_workspace_id, loggedin_user_id, output_item_id, "is_uploaded", True
#     )


async def check_workflow_validity(
    selected_workspace_id: str,
    loggedin_user_id: str,
    output_item_id: str,
    file_paths: List[str],
    extraction_path: str,
):
    # Check for workflow.py among the extracted file paths using the same path format.
    # file_paths strips the leading item_title/ prefix, so workflow.py sits directly under extraction_path.
    workflow_file_path = f"{extraction_path}/workflow.py"

    if workflow_file_path not in file_paths:
        db = next(get_dashboard_db())

        workflow_service = WorkflowService(db)
        workflows_response = workflow_service.fetch_workflows_by_ids(
            selected_workspace_id, loggedin_user_id, [output_item_id]
        )
        workflow = workflows_response[0]

        updated_flow = WorkflowSchema(
            id=workflow.id,
            s3_key=workflow.s3_key,
            flow_function_name=workflow.flow_function_name,
            deployment_id=workflow.deployment_id,
            deployment_name=workflow.deployment_name,
            flow_id=workflow.flow_id,
            status="inactive",
            is_valid=False,
            parameter_schema=workflow.parameter_schema,
        )
        workflow_service.update_workflow(
            selected_workspace_id, loggedin_user_id, updated_flow
        )
        raise ValueError("------->>>>>>Not a valid workflow directory.")


async def extract_zip_workflow_with_folder_structure(
    loggedin_user_id: str,
    selected_workspace_id: str,
    input_item_id: str,
    output_item_id: str,
):
    """
    Main workflow for extracting zip files.

    Steps:
    1. Prepare extraction
    2. Download zip from S3
    3. Extract files locally
    4. Build file paths and urls
    5. Check workflow validity
    6. Upload extracted files to S3
    7: Update workflow status
    8. Clean up temporary files
    """
    db = next(get_dashboard_db())
    job_service = JobService(db)
    job_id = await job_service.get_job_id_by_output_item_id(
        selected_workspace_id, loggedin_user_id, output_item_id
    )
    update_job_steps_progress = UpdateJobStepsProgress(
        selected_workspace_id, loggedin_user_id, job_id
    )
    
    # Step 1: Prepare extraction
    response = await prepare_extraction(
        loggedin_user_id,
        selected_workspace_id,
        input_item_id,
    )
    update_job_steps_progress.update(1)

    download_path = (
        response.file_download_path
    )  # path where the file will be downloaded e.g. "./work_dir/some_unique_folder/file.zip"
    extraction_path = (
        response.file_extraction_path
    )  # path where the zip file will be extracted e.g. "./work_dir/some_unique_folder/"
    item_title = response.item_title
    file_s3_key = response.file_s3_key

    # Step 2: Download zip from S3
    await download_file_from_s3(
        file_s3_key,
        download_path,
    )
    update_job_steps_progress.update(2)

    # Step 3: Extract files locally
    file_list_extracted = extract_zip_file(download_path, extraction_path)
    update_job_steps_progress.update(3)

    # Step 4: Build file paths and urls
    response = await build_file_paths_and_urls(
        loggedin_user_id,
        selected_workspace_id,
        item_title,
        output_item_id,
        file_list_extracted,
        extraction_path,
    )
    update_job_steps_progress.update(4)

    file_paths = response.get(
        "file_paths"
    )  # ["./work_dir/some_unique_folder/", "./work_dir/some_unique_folder/file1.txt", "./work_dir/some_unique_folder/file2.txt"]
    file_urls = response.get("file_urls")  # ["", "file1.txt", "file2.txt"]

    # Step 5: Check workflow validity
    await check_workflow_validity(
        selected_workspace_id, loggedin_user_id, output_item_id, file_paths, extraction_path
    )
    update_job_steps_progress.update(5)

    # Step 6: Upload extracted files to S3
    upload_files_to_s3(file_paths, file_urls)
    update_job_steps_progress.update(6)

    # await update_upload_status(selected_workspace_id, loggedin_user_id, output_item_id)

    # Step 7: Update workflow
    await update_workflow(selected_workspace_id, loggedin_user_id, output_item_id)
    update_job_steps_progress.update(7)

    # Step 8: Cleanup (optional task)
    cleanup_temp_files(extraction_path)
    update_job_steps_progress.update(8)


if __name__ == "__main__":
    import asyncio
    import os

    asyncio.run(
        extract_zip_workflow_with_folder_structure(
            loggedin_user_id=os.environ["loggedin_user_id"],
            selected_workspace_id=os.environ["selected_workspace_id"],
            input_item_id=os.environ["input_item_id"],
            output_item_id=os.environ["output_item_id"],
        )
    )
