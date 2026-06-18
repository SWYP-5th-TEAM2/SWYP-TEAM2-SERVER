from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.exceptions import TokenMissingException
from app.core.security.jwt import decode_access_token, get_subject

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user_id(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> UUID:
    if credentials is None:
        raise TokenMissingException()

    token = credentials.credentials

    payload = decode_access_token(str(token))
    return get_subject(payload=payload)