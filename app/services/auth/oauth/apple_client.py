import asyncio
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    InvalidKeyError,
    InvalidTokenError,
    PyJWKClientError,
)

from app.config import settings
from app.core.exceptions import (
    AppleOAuthConfigurationException,
    AuthorizationCodeExpiredException,
    AuthorizationCodeMissingException,
    ExternalAuthServiceUnavailableException,
    RequiredUserInfoMissingException,
    SocialLoginFailedException,
)
from app.models.user.enums import Provider
from app.services.auth.oauth.base import OAuthClient, OAuthUserInfo

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS_URL = f"{APPLE_ISSUER}/auth/keys"
APPLE_TOKEN_URL = f"{APPLE_ISSUER}/auth/token"
APPLE_HTTP_TIMEOUT = 5.0
APPLE_CLIENT_SECRET_LIFETIME = timedelta(minutes=5)

apple_jwk_client = PyJWKClient(
    APPLE_JWKS_URL,
    timeout=APPLE_HTTP_TIMEOUT,
)


def _require_apple_settings() -> tuple[str, str, str, str]:
    team_id = (settings.apple_team_id or "").strip()
    client_id = (settings.apple_client_id or "").strip()
    key_id = (settings.apple_key_id or "").strip()
    private_key = (settings.apple_private_key or "").replace("\\n", "\n").strip()

    if not team_id or not client_id or not key_id or not private_key:
        raise AppleOAuthConfigurationException()

    return team_id, client_id, key_id, private_key


def _create_apple_client_secret() -> tuple[str, str]:
    team_id, client_id, key_id, private_key = _require_apple_settings()
    issued_at = datetime.now(timezone.utc)

    try:
        client_secret = jwt.encode(
            {
                "iss": team_id,
                "iat": issued_at,
                "exp": issued_at + APPLE_CLIENT_SECRET_LIFETIME,
                "aud": APPLE_ISSUER,
                "sub": client_id,
            },
            private_key,
            algorithm="ES256",
            headers={"kid": key_id},
        )
    except (InvalidKeyError, InvalidTokenError, ValueError, TypeError):
        raise AppleOAuthConfigurationException()

    return client_id, client_secret


async def _exchange_apple_authorization_code(
    code: str,
) -> dict[str, Any]:
    normalized_code = code.strip()
    if not normalized_code:
        raise AuthorizationCodeMissingException()

    client_id, client_secret = _create_apple_client_secret()

    try:
        async with httpx.AsyncClient(timeout=APPLE_HTTP_TIMEOUT) as client:
            response = await client.post(
                APPLE_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": normalized_code,
                    "grant_type": "authorization_code",
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
    except httpx.HTTPError:
        raise ExternalAuthServiceUnavailableException()

    if response.status_code != 200:
        try:
            error = response.json().get("error")
        except (ValueError, AttributeError):
            error = None

        if error == "invalid_grant":
            raise AuthorizationCodeExpiredException()
        if error == "invalid_client":
            raise AppleOAuthConfigurationException()
        raise SocialLoginFailedException()

    try:
        body = response.json()
    except ValueError:
        raise SocialLoginFailedException()

    if not isinstance(body, dict):
        raise SocialLoginFailedException()

    return body


async def _get_user_info_from_identity_token(
    identity_token: str,
) -> OAuthUserInfo:
    _, client_id, _, _ = _require_apple_settings()

    try:
        signing_key = await asyncio.to_thread(
            apple_jwk_client.get_signing_key_from_jwt,
            identity_token,
        )
        payload = jwt.decode(
            identity_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=APPLE_ISSUER,
        )
    except (InvalidTokenError, PyJWKClientError, ValueError, TypeError):
        raise SocialLoginFailedException()

    provider_id = payload.get("sub")
    if not isinstance(provider_id, str) or not provider_id:
        raise RequiredUserInfoMissingException()

    email = payload.get("email")
    return OAuthUserInfo(
        provider=Provider.APPLE,
        provider_id=provider_id,
        email=email if isinstance(email, str) else None,
        nickname=None,
    )


class AppleOAuthClient(OAuthClient):
    async def get_access_token(self, code: str) -> str:
        token_response = await _exchange_apple_authorization_code(code)
        identity_token = token_response.get("id_token")
        if not isinstance(identity_token, str) or not identity_token:
            raise SocialLoginFailedException()
        return identity_token

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        return await _get_user_info_from_identity_token(access_token)

    async def authenticate_token(
        self,
        token: str,
        code: str | None = None,
    ) -> OAuthUserInfo:
        normalized_token = token.strip()
        if not normalized_token:
            raise SocialLoginFailedException()
        if code is None or not code.strip():
            raise AuthorizationCodeMissingException()

        # 앱이 전달한 ID Token과 authorization code 교환으로 받은 ID Token 검증
        initial_user_info = await _get_user_info_from_identity_token(
            normalized_token,
        )
        token_response = await _exchange_apple_authorization_code(code)
        exchanged_identity_token = token_response.get("id_token")
        if (
            not isinstance(exchanged_identity_token, str)
            or not exchanged_identity_token
        ):
            raise SocialLoginFailedException()

        exchanged_user_info = await _get_user_info_from_identity_token(
            exchanged_identity_token,
        )

        # 두 Token의 Apple 사용자 식별자(sub)가 동일할 때만 로그인
        if not hmac.compare_digest(
            initial_user_info.provider_id,
            exchanged_user_info.provider_id,
        ):
            raise SocialLoginFailedException()

        return OAuthUserInfo(
            provider=Provider.APPLE,
            provider_id=exchanged_user_info.provider_id,
            email=exchanged_user_info.email or initial_user_info.email,
            nickname=None,
        )
