from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from storage import get_bytes

router = APIRouter(prefix="/evidence", tags=["evidence"])

@router.get("/{key:path}")
def get_evidence(key: str):
    try:
        data = get_bytes(key)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Not found") from e
    return Response(content=data, media_type="application/octet-stream")
