from typing import List
from pydantic import BaseModel
from uuid import uuid4
import zipfile
import shutil
import os

# import core
from app.core.dashboard_database import get_dashboard_db
# from app.core.prefect_database import get_prefect_db
from app.core.config import get_settings

# import services
from app.services.job import JobService
from app.services.file import FileService
from app.services.item import ItemService
from app.services.s3_client import S3ClientService


settings = get_settings()

work_dir = "./work_dir"


class FilePathsAndUrlsResponse(BaseModel):
    file_paths: List[str]
    file_urls: List[str]


class PrepareCompressionResponse(BaseModel):
    file_paths: List[str]
    file_urls: List[str]
    file_download_path: str
    directory_to_zip: str
    compressed_zip_path: str
    output_file_url: str


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


async def get_file_paths_and_urls(
    loggedin_user_id: str,
    selected_workspace_id: str,
    item_id: str,
    item_title,
) -> FilePathsAndUrlsResponse:
    db = next(get_dashboard_db())
    # prefect_db = next(get_prefect_db())

    paths = [f"{item_title}/"]
    file_urls = [""]

    file_service = FileService(
        db,
        # prefect_db
    )
    item_service = ItemService(db)

    async def _get_files_by_field_name_field_val(
        loggedin_user_id: str,
        selected_workspace_id: str,
        item_id: str,
        path_prefix: str,
        paths: List[str],
        file_urls: List[str],
    ) -> List[str]:
        files = file_service.get_files_by_field_name_field_val(
            selected_workspace_id,
            loggedin_user_id,
            "parent",
            item_id,
        )
        ids = [file.id for file in files]

        if len(ids) > 0:
            for file in files:
                child_id = file.id
                items = item_service.fetch_items_by_ids(
                    selected_workspace_id, loggedin_user_id, [child_id]
                )
                item = items[0]
                file_url = file.url
                mime_type = file.mime_type or ""
                title = item.title
                is_folder = mime_type == "vcollab_folder"

                if is_folder:
                    path = f"{path_prefix}{title}/"
                elif title.endswith(f".{mime_type}"):
                    path = f"{path_prefix}{title}"
                else:
                    path = f"{path_prefix}{title}.{mime_type}" if mime_type else f"{path_prefix}{title}"

                paths.append(path)
                file_urls.append(file_url)

                if is_folder:
                    await _get_files_by_field_name_field_val(
                        loggedin_user_id,
                        selected_workspace_id,
                        child_id,
                        path,
                        paths,
                        file_urls,
                    )

    await _get_files_by_field_name_field_val(
        loggedin_user_id,
        selected_workspace_id,
        item_id,
        f"{item_title}/",
        paths,
        file_urls,
    )
    return FilePathsAndUrlsResponse(file_paths=paths, file_urls=file_urls)


async def prepare_compression(
    selected_workspace_id: str,
    loggedin_user_id: str,
    input_item_id: str,
    output_item_id: str,
):
    db = next(get_dashboard_db())
    # prefect_db = next(get_prefect_db())

    file_service = FileService(
        db,
        # prefect_db
    )
    item_service = ItemService(db)

    # get the url of output file
    files_response = file_service.fetch_files_by_ids(
        selected_workspace_id,
        loggedin_user_id,
        [output_item_id],
    )
    output_file = files_response[0]
    output_file_url = output_file.url

    # get the title of input file
    items_response = item_service.fetch_items_by_ids(
        selected_workspace_id, loggedin_user_id, [input_item_id]
    )
    input_item = items_response[0]
    input_item_title = input_item.title

    # We download the files from s3 and save them in the same directory structure as of the folder we are going to zip
    # So to create a similar folder structure, we get file paths and corresponding file urls for downloading from s3 bucket
    # e.g. file_paths = ["folder1/", "folder1/file1.txt", "folder1/file2.txt", "folder1/folder2/", "folder1/folder2/file3.txt"]
    # file_urls = ["", "some_key1.txt", "some_key2.txt", "", "some_key3.txt"]
    # file_url corresponding to a folder is empty, because we don't need to upload anything to bucket for a folder
    file_paths_and_urls_resp = await get_file_paths_and_urls(
        loggedin_user_id,
        selected_workspace_id,
        str(input_item_id),
        input_item_title,
    )
    file_paths = file_paths_and_urls_resp.file_paths
    file_urls = file_paths_and_urls_resp.file_urls

    unique_id = uuid4()
    # work_dir = "./work_dir"
    # create a unique folder inside "./workdir/"
    unique_folder_in_work_dir = f"{work_dir}/{unique_id}"
    # folder where all the files will be downloading before zipping
    file_download_path = unique_folder_in_work_dir

    # folder path which will be zipped after downloading all the file
    directory_to_zip = f"{file_download_path}/{file_paths[0].split('/')[0]}"

    # path where the compressed zip will be saved before saving back to s3 bucket
    compressed_zip_path = f"{unique_folder_in_work_dir}/{unique_id}.zip"

    return PrepareCompressionResponse(
        file_paths=file_paths,
        file_urls=file_urls,
        file_download_path=file_download_path,
        directory_to_zip=directory_to_zip,
        compressed_zip_path=compressed_zip_path,
        output_file_url=output_file_url,
    )


def download_file_from_s3(file_s3_key: str, download_path: str) -> None:
    """Download file from S3 with automatic retries."""
    # Create local download path directory if it doesn't exist
    s3_client = S3ClientService()
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    s3_client.download_file_to_local_path(file_s3_key, download_path)


def download_s3_objects(
    file_paths: List[str], file_urls: List[str], file_download_path: str
):
    for file_path, s3_key in zip(file_paths, file_urls):
        if s3_key and not file_path.endswith("/"):
            download_path = f"{file_download_path}/{file_path}"
            download_file_from_s3(s3_key, download_path)
    print("s3 download complete>>>>>>>")

def cleanup_temp_files(path: str):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    print("cleanup complete>>>>")


def zip_directory(source_dir: str, output_zip: str):
    source_dir = os.path.abspath(source_dir)
    output_zip = os.path.abspath(output_zip)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Preserve empty directories by writing a directory entry
            for d in dirs:
                dir_full_path = os.path.join(root, d)
                arcname = os.path.relpath(dir_full_path, source_dir) + "/"
                zipf.writestr(zipfile.ZipInfo(arcname), "")
            for file in files:
                full_path = os.path.join(root, file)

                # Preserve relative path inside the zip
                arcname = os.path.relpath(full_path, source_dir)

                zipf.write(full_path, arcname)
    print("zip directory complete>>>>")

def upload_zip_to_s3(zip_path: str, s3_key: str):
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"File not found: {zip_path}")

    s3_client = S3ClientService()
    s3_client.upload_local_file(zip_path, s3_key)


def update_upload_status(
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
    print("update upload status complete>>>>")


async def compress_file_workflow(
    selected_workspace_id: str,
    loggedin_user_id: str,
    input_item_id: str,
    output_item_id: str,
):
    """
    Main workflow for compressing a folder to zip.

    Steps:
    1. Prepare file compress (get file_paths, file_urls and other details)
    2. Download objects to be zipped from s3 bucket
    3. Zip downloaded objects
    4. upload the zipped file back to s3 bucket
    5. update database
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
    # Step 1: Prepare file compress (get file_paths, file_urls and other details)
    response = await prepare_compression(
        selected_workspace_id,
        loggedin_user_id,
        input_item_id,
        output_item_id,
    )
    update_job_steps_progress.update(1)

    file_paths = (
        response.file_paths
    )  # ["folder1/", "folder1/file1.txt", "folder1/file2.txt", "folder1/folder2/", "folder1/folder2/file3.txt"]

    file_urls = (
        response.file_urls
    )  # ["", "s3_key1.txt", "s3_key2.txt", "", "s3_key3.txt"]

    file_download_path = response.file_download_path  # "./work_dir/some_unique_id/"

    directory_to_zip = response.directory_to_zip  # "./work_dir/some_unique_id/folder1/"

    compressed_zip_path = (
        response.compressed_zip_path
    )  # "./work_dir/some_unique_id.zip"

    output_file_url = response.output_file_url

    # Step 2: download all files from s3 bucket while maintaining the folder structure
    download_s3_objects(file_paths, file_urls, file_download_path)
    update_job_steps_progress.update(2)

    # Step 3: zip all the downloaded files
    zip_directory(directory_to_zip, compressed_zip_path)
    update_job_steps_progress.update(3)

    # Step 4: upload the zipped file back to s3 bucket
    upload_zip_to_s3(compressed_zip_path, output_file_url)
    update_job_steps_progress.update(4)

    # Step 5: update file upload status in database
    update_upload_status(selected_workspace_id, loggedin_user_id, output_item_id)
    update_job_steps_progress.update(5)

    # Step 6: Clean up temporary files
    cleanup_temp_files(file_download_path)
    update_job_steps_progress.update(6)


if __name__ == "__main__":
    import asyncio
    import os

    asyncio.run(
        compress_file_workflow(
            loggedin_user_id=os.environ["loggedin_user_id"],
            selected_workspace_id=os.environ["selected_workspace_id"],
            input_item_id=os.environ["input_item_id"],
            output_item_id=os.environ["output_item_id"],
        )
    )
