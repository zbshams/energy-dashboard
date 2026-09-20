from fastapi import HTTPException, Header, Depends
from typing import Optional
from app.config import VALID_API_KEYS

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key from X-API-Key header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key
