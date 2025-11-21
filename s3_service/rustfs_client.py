import boto3
from config.settings import settings
from botocore.client import Config

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.RUSTFS_ENDPOINT,  # http://localhost:9000
        aws_access_key_id=settings.RUSTFS_ACCESS_KEY,
        aws_secret_access_key=settings.RUSTFS_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"  # RustFS accepts any region
    )


def get_public_url(object_name: str):
    return f"{settings.RUSTFS_ENDPOINT}/{settings.RUSTFS_BUCKET}/{object_name}"
