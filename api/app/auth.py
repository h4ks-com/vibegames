import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.settings import settings

security = HTTPBearer()


def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token: str = credentials.credentials
    if not any(secrets.compare_digest(token, key) for key in settings.API_KEYS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key.")
    return token
