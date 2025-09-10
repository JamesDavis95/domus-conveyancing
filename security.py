import os
from fastapi import Header, HTTPException

API_KEY = os.getenv("APP_API_KEY")

async def require_key(x_api_key: str = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "Invalid or missing API key")
