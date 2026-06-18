import uuid
from datetime import datetime, timezone, timedelta
from typing import Literal, Any
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config import settings
from app.core.exceptions import TokenExpiredException, InvalidTokenException, InvalidTokenTypeException
from app.schemas.auth import TokenResponse


TokenType = Literal["access", "refresh"]

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_access_token(user_id: UUID | str) -> str:
    now = _now()
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _create_refresh_token(user_id: UUID | str) -> str:
    now = _now()
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        'type': "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_tokens(user_id: UUID | str) -> TokenResponse:
    return TokenResponse(
        access_token=_create_access_token(user_id),
        refresh_token=_create_refresh_token(user_id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


def _decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError:
        raise TokenExpiredException()
    except InvalidTokenError:
        raise InvalidTokenException()


def _validate_token_type(payload: dict[str, Any], expected_type: TokenType) -> None:
    actual_type = payload.get("type")

    if actual_type != expected_type:
        raise InvalidTokenTypeException()


def decode_access_token(token: str) -> dict[str, Any]:
    payload = _decode_token(token)
    _validate_token_type(payload, "access")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    payload = _decode_token(token)
    _validate_token_type(payload, "refresh")
    return payload


def get_subject(payload: dict[str, Any]) -> UUID:
    subject = payload.get("sub")

    if subject is None:
        raise InvalidTokenException()

    try:
        return UUID(str(subject))
    except ValueError:
        raise InvalidTokenException()


def get_jti(payload: dict[str, Any]) -> str:
    jti = payload.get("jti")

    if jti is None:
        raise InvalidTokenException()
    return str(jti)

