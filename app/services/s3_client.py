import boto3
from typing import List
from datetime import datetime, timedelta
from app.core.config import get_settings

settings = get_settings()


class S3ClientService:
    def __init__(self):
        self.bucket = settings.aws_s3_bucket
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key,
            aws_secret_access_key=settings.aws_secret_key,
            region_name=settings.aws_region,
        )

    def delete_object(self, file_key: str):
        self.client.delete_object(
            Bucket=self.bucket,
            Key=file_key,
        )

    def generate_presigned_url_for_get_object(
        self, file_key: str, file_name: str
    ) -> str:
        params = {
            "Bucket": self.bucket,
            "Key": file_key,
            "ResponseContentDisposition": f'attachment; filename="{file_name}"',
        }
        return self.client.generate_presigned_url(
            "get_object", Params=params, ExpiresIn=900
        )

    def create_multipart_upload(self, file_name: str):
        return self.client.create_multipart_upload(
            Bucket=self.bucket,
            Expires=datetime.now() + timedelta(minutes=1440),
            Key=file_name,
        )

    def generate_presigned_url_for_put_object(
        self, key: str, uploadId: str, partNumber: int
    ):
        presigned_url = self.client.generate_presigned_url(
            "upload_part",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "UploadId": uploadId,
                "PartNumber": partNumber,
            },
            ExpiresIn=3600,
            HttpMethod="PUT",
        )
        return presigned_url

    def complete_multipart_upload_s3(
        self, key: str, uploadId: str, partsToCommit: List
    ):
        self.client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=key,
            MultipartUpload={"Parts": partsToCommit},
            UploadId=uploadId,
        )

    def head_object(self, object_key: str):
        return self.client.head_object(Bucket=self.bucket, Key=object_key)

    def download_file_to_local_path(self, object_key: str, download_path: str):
        self.client.download_file(self.bucket, object_key, download_path)

    def upload_local_file(self, file_path: str, object_key: str):
        self.client.upload_file(
            Filename=file_path,
            Bucket=self.bucket,
            Key=object_key,
        )
