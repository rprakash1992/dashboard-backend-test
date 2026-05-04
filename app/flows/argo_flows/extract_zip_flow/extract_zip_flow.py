from typing import Any, List, Optional
from pydantic import BaseModel
from uuid import uuid4
import zipfile
import asyncio
import shutil
import os

# import core
from app.core.dashboard_database import get_dashboard_db

# from app.core.prefect_database import get_prefect_db
from app.core.config import get_settings

# import schemas
from app.schemas.item import ItemSchema
from app.schemas.file import FileSchema

# import services
from app.services.job import JobService
from app.services.item import ItemService
from app.services.file import FileService
from app.services.s3_client import S3ClientService


settings = get_settings()

work_dir = "./work_dir"


class ParentData(BaseModel):
    parent: Optional[int] = None
    isFolder: bool


class ItemsAndParentsDataResponse(BaseModel):
    items_titles: List[str]
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


def remove_slash(file_name: str) -> str:
    ret_val = ""
    arr = file_name.split("/")

    if "/" in file_name and file_name.rfind("/") == len(file_name) - 1:
        # ends with "/"
        ret_val = arr[-2]
    elif "/" in file_name and file_name.rfind("/") != len(file_name) - 1:
        ret_val = arr[-1]
    else:
        ret_val = file_name

    return ret_val


def get_index_of_parent(file_list: List[str], file: str) -> Optional[int]:
    """Return the index of the parent entry in file_list, or None if the file is at root level."""
    if "/" not in file:
        # Top-level file/folder: parent is the root item at index 0
        return 0

    # Strip trailing slash to get the logical path
    logical = file[:-1] if file.endswith("/") else file

    # Parent path is everything up to and including the last "/" of the logical path
    last_slash = logical.rfind("/")
    if last_slash <= 0:
        # Directly under root
        return 0

    parent = logical[:last_slash + 1]
    try:
        return file_list.index(parent)
    except ValueError:
        # Parent folder entry missing from zip (e.g. zip was created without explicit folder entries)
        return 0


def get_items_titles_and_parents_data(
    file_list: List[str], file_title: str
) -> ItemsAndParentsDataResponse:
    parents_data = []
    items_titles = []

    for index, file in enumerate(file_list):
        new_parent = {
            "parent": None if index == 0 else get_index_of_parent(file_list, file),
            "isFolder": file.rfind("/") == len(file) - 1,
        }

        parents_data.append(new_parent)
        items_titles.append(file_title if index == 0 else remove_slash(file))

    return ItemsAndParentsDataResponse(
        items_titles=items_titles, parents_data=parents_data
    )


# @task(name="get-files-data")
def get_files_data(
    items_titles: List[Any],
    file_list: List[str],
    parents_data: List[ParentData],
) -> List[Any]:
    files_data = []

    for index, item_title in enumerate(items_titles):
        is_folder = parents_data[index].isFolder
        entry = file_list[index]

        if is_folder:
            ext = ""
            url = ""
        else:
            filename = entry.split("/")[-1]
            ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
            url = f"{str(uuid4())}.{ext}" if ext else str(uuid4())

        files_data.append(
            {
                "title": item_title,
                "description": "",
                "image": "",
                "tags": [],
                "file_extension": "vcollab_folder" if is_folder else ext,
                "is_uploaded": True,
                "parent": None,
                "url": url,
            }
        )

    return files_data


def update_files_parent(
    selected_workspace_id: str,
    loggedin_user_id: str,
    items_data: List[ItemSchema],
    parents_data: List[ParentData],
):
    db = next(get_dashboard_db())
    # prefect_db = next(get_prefect_db())
    file_service = FileService(
        db,
        # prefect_db
    )

    for index, item in enumerate(items_data):
        parent_index = parents_data[index].parent
        parent_id = (
            items_data[parent_index].id
            if parent_index is not None and 0 <= parent_index < len(items_data)
            else None
        )

        file_service.update_file_field_by_id(
            selected_workspace_id,
            loggedin_user_id,
            item.id,
            "parent",
            parent_id,
        )


async def update_database_records(
    loggedin_user_id: str,
    selected_workspace_id: str,
    item_title: str,
    output_item_id: Any,
    file_list_extracted: list[str],
    extraction_path: str,
):
    """Update database with extracted file records."""
    # Create new DB session
    db = next(get_dashboard_db())
    # prefect_db = next(get_prefect_db())

    # Your database update logic here
    # Add items and files to database
    # file_list is the list of file inside the zip
    # for e.g ["folder1/", "folder1/file.txt", "folder1/file2.txt", "folder1/folder2/", "folder1/folder2/file3.txt"]
    file_list = [f"{item_title}/"]
    for item in file_list_extracted:
        file_list.append(f"{item_title}/{item}")

    items_titles_and_parents_data = get_items_titles_and_parents_data(
        file_list, item_title
    )

    # items_data has all the items for the folder, sub folder and sub folder items which are to be added to items table
    items_titles = items_titles_and_parents_data.items_titles
    # parents data is used to maintain the same folder structure as the zip file in the frontend
    # the files which are inside a folder will have a "parent" field pointing to the metadata id of parent folder item
    parents_data = items_titles_and_parents_data.parents_data

    # get the output item using output_item_id
    # output item is the root folder item for the extracted zip, which we have already added to items and files table
    item_service = ItemService(db)
    items_response = item_service.fetch_items_by_ids(
        selected_workspace_id,
        loggedin_user_id,
        [output_item_id],
    )
    output_item = items_response[0]

    file_service = FileService(
        db,
        # prefect_db
    )
    files_response = file_service.fetch_files_by_ids(
        selected_workspace_id,
        loggedin_user_id,
        [output_item_id],
    )
    output_file = files_response[0]

    # get files_data corresponding to each item
    new_files_data = get_files_data(items_titles, file_list, parents_data)

    # add all the files to files table
    files_data: List[FileSchema] = [output_file]
    items_data: List[ItemSchema] = [output_item]

    for new_file_data in new_files_data[1:]:
        response = file_service.insert_file(
            selected_workspace_id,
            loggedin_user_id,
            new_file_data.get("title"),
            new_file_data.get("description"),
            new_file_data.get("image"),
            new_file_data.get("tags"),
            new_file_data.get("file_extension"),
            new_file_data.get("is_uploaded"),
            new_file_data.get("parent"),
            new_file_data.get("url"),
        )
        items_data.append(response.item)
        files_data.append(response.file)

    update_files_parent(
        selected_workspace_id,
        loggedin_user_id,
        items_data,
        parents_data,
    )

    # paths to local extracted files which have to be uploaded back to s3 bucket
    file_paths = [
        f"{extraction_path}/{item[item.find('/') + 1:]}" for item in file_list
    ]
    # uniquely generated s3 keys for the files to be uploaded
    file_urls = [file_data.url for file_data in files_data]

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
        selected_workspace_id,
        loggedin_user_id,
        [input_item_id],
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


async def update_upload_status(
    selected_workspace_id: str, loggedin_user_id: str, output_item_id: str
):
    db = next(get_dashboard_db())
    # prefect_db = next(get_prefect_db())

    file_service = FileService(
        db,
        # prefect_db
    )

    file_service.update_file_field_by_id(
        selected_workspace_id,
        loggedin_user_id,
        output_item_id,
        "is_uploaded",
        True,
    )


async def extract_zip_workflow(
    loggedin_user_id: str,
    selected_workspace_id: str,
    input_item_id: str,
    output_item_id: str,
):
    """
    Main workflow for extracting zip files.

    Steps:
    1. Download zip from S3
    2. Extract files locally
    3. Update database records
    3. Upload extracted files to S3
    5: Update upload status
    6. Clean up temporary files
    """
    db = next(get_dashboard_db())
    job_service = JobService(db)
    job_id = await job_service.get_job_id_by_output_item_id(
        selected_workspace_id, loggedin_user_id, output_item_id
    )
    update_job_steps_progress = UpdateJobStepsProgress(
        selected_workspace_id, loggedin_user_id, job_id
    )

    prepare_extract_response = await prepare_extraction(
        loggedin_user_id,
        selected_workspace_id,
        input_item_id,
    )
    update_job_steps_progress.update(1)

    download_path = (
        prepare_extract_response.file_download_path
    )  # path where the file will be downloaded e.g. "./work_dir/some_unique_folder/file.zip"
    extraction_path = (
        prepare_extract_response.file_extraction_path
    )  # path where the zip file will be extracted e.g. "./work_dir/some_unique_folder/"
    item_title = prepare_extract_response.item_title
    file_s3_key = prepare_extract_response.file_s3_key

    # Step 1: Download
    await download_file_from_s3(
        file_s3_key,
        download_path,
    )
    update_job_steps_progress.update(2)

    # Step 2: Extract files locally
    file_list_extracted = extract_zip_file(download_path, extraction_path)
    update_job_steps_progress.update(3)

    # Step 3: Update database records
    update_database_response = await update_database_records(
        loggedin_user_id,
        selected_workspace_id,
        item_title,
        output_item_id,
        file_list_extracted,
        extraction_path,
    )
    update_job_steps_progress.update(4)

    file_paths = update_database_response.get(
        "file_paths"
    )  # ["./work_dir/some_unique_folder/", "./work_dir/some_unique_folder/file1.txt", "./work_dir/some_unique_folder/file2.txt"]
    file_urls = update_database_response.get(
        "file_urls"
    )  # ["", "file1.txt", "file2.txt"]

    # Step 4: Upload extracted files to S3
    upload_files_to_s3(file_paths, file_urls)
    update_job_steps_progress.update(5)

    # Step 5: Update upload status
    await update_upload_status(selected_workspace_id, loggedin_user_id, output_item_id)
    update_job_steps_progress.update(6)

    # Step 6: Clean up temporary files
    cleanup_temp_files(extraction_path)
    update_job_steps_progress.update(7)


if __name__ == "__main__":
    import os

    asyncio.run(
        extract_zip_workflow(
            loggedin_user_id=os.environ["loggedin_user_id"],
            selected_workspace_id=os.environ["selected_workspace_id"],
            input_item_id=os.environ["input_item_id"],
            output_item_id=os.environ["output_item_id"],
        )
    )
