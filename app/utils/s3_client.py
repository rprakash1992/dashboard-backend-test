import boto3
from app.core.config import get_settings

settings = get_settings()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.aws_access_key,
    aws_secret_access_key=settings.aws_secret_key,
    region_name=settings.aws_region,
)
