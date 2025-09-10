import boto3
from settings import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name=settings.S3_REGION,
)

def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    _s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)

def get_bytes(key: str) -> bytes:
    obj = _s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return obj["Body"].read()
