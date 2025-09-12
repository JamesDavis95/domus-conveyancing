import os, uuid, pathlib
from typing import Optional

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "./data/uploads")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _s3_client():
    import boto3, botocore
    endpoint = os.getenv("S3_ENDPOINT") or os.getenv("MINIO_ENDPOINT")
    params = {}
    if endpoint:
        params["endpoint_url"] = endpoint
    ak = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("MINIO_ACCESS_KEY")
    sk = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("MINIO_SECRET_KEY")
    if ak and sk:
        params["aws_access_key_id"] = ak
        params["aws_secret_access_key"] = sk
    region = os.getenv("AWS_REGION") or os.getenv("S3_REGION")
    if region:
        params["region_name"] = region
    try:
        return boto3.client("s3", **params)
    except Exception:
        return None

def store_bytes(content: bytes, *, prefix: str = "", filename: Optional[str] = None) -> dict:
    """
    Returns {"backend":"local|s3","path":local_path, "bucket":..., "key":...}
    """
    bucket = os.getenv("S3_BUCKET") or os.getenv("MINIO_BUCKET")
    if bucket:
        s3 = _s3_client()
        if s3:
            key = f"{prefix.strip('/')+'/' if prefix else ''}{uuid.uuid4().hex}-{(filename or 'file')}"
            s3.put_object(Bucket=bucket, Key=key, Body=content, ContentType="application/pdf")
            return {"backend":"s3","bucket":bucket,"key":key,"path":f"s3://{bucket}/{key}"}
    # local fallback
    sub = DATA_DIR / (prefix.strip("/") if prefix else "")
    sub.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}-{(filename or 'file')}"
    p = sub / name
    p.write_bytes(content)
    return {"backend":"local","path":str(p)}

def fetch_to_tmp(obj: dict) -> str:
    """
    Given store_bytes result, fetch to a local temp path and return it.
    """
    import tempfile, shutil
    if not obj: raise FileNotFoundError("empty storage object")
    if obj.get("backend") == "s3":
        s3 = _s3_client()
        if not s3: raise FileNotFoundError("s3 client unavailable")
        bucket, key = obj["bucket"], obj["key"]
        tmp = tempfile.NamedTemporaryFile(delete=False)
        s3.download_fileobj(bucket, key, tmp)
        tmp.close()
        return tmp.name
    # local
    p = obj.get("path")
    if not p or not os.path.exists(p):
        raise FileNotFoundError("local path missing")
    tmp = tempfile.NamedTemporaryFile(delete=False)
    with open(p, "rb") as f, open(tmp.name, "wb") as o:
        shutil.copyfileobj(f, o)
    return tmp.name
