import asyncio

import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError

from app.config import settings
from app.core.exceptions import SocialLoginFailedException, RequiredUserInfoMissingException
from app.models.user.enums import Provider
from app.services.auth.oauth.base import OAuthClient, OAuthUserInfo

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
GOOGLE_HTTP_TIMEOUT = 5.0
google_jwk_client = PyJWKClient(
    GOOGLE_JWKS_URL,
    timeout=GOOGLE_HTTP_TIMEOUT,
)

class GoogleOAuthClient(OAuthClient):
    async def get_access_token(self, code: str) -> str:
        data = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=GOOGLE_HTTP_TIMEOUT) as client:
                response = await client.post(
                    url=GOOGLE_TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except httpx.HTTPError:
            raise SocialLoginFailedException()

        if response.status_code != 200:
            print("Google token error status:", response.status_code)
            print("Google token error body:", response.text)
            raise SocialLoginFailedException()

        body = response.json()
        access_token = body.get("access_token")

        if not isinstance(access_token, str) or not access_token:
            raise SocialLoginFailedException()

        return access_token


    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        try:
            async with httpx.AsyncClient(timeout=GOOGLE_HTTP_TIMEOUT) as client:
                response = await client.get(
                    url=GOOGLE_USER_INFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.HTTPError:
            raise SocialLoginFailedException()

        if response.status_code != 200:
            raise SocialLoginFailedException()

        body = response.json()

        provider_id = body.get("sub")
        email = body.get("email")
        nickname = body.get("name")

        if provider_id is None:
            raise RequiredUserInfoMissingException()

        return OAuthUserInfo(
            provider=Provider.GOOGLE,
            provider_id=str(provider_id),
            email=email if isinstance(email, str) else None,
            nickname=nickname if isinstance(nickname, str) else None,
        )

    async def authenticate_token(
        self,
        token: str,
        code: str | None = None,
    ) -> OAuthUserInfo:
        normalized_token = token.strip()
        if not normalized_token:
            raise SocialLoginFailedException()

        try:
            # PyJWKClient의 네트워크 조회는 동기 방식이므로 이벤트 루프 밖에서 실행한다.
            signing_key = await asyncio.to_thread(
                google_jwk_client.get_signing_key_from_jwt,
                normalized_token,
            )
            payload = jwt.decode(
                normalized_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.google_client_id,
            )
        except (InvalidTokenError, PyJWKClientError, ValueError):
            raise SocialLoginFailedException()

        if payload.get("iss") not in GOOGLE_ISSUERS:
            raise SocialLoginFailedException()

        provider_id = payload.get("sub")
        email = payload.get("email")
        nickname = payload.get("name")

        if provider_id is None:
            raise RequiredUserInfoMissingException()

        return OAuthUserInfo(
            provider=Provider.GOOGLE,
            provider_id=str(provider_id),
            email=email if isinstance(email, str) else None,
            nickname=nickname if isinstance(nickname, str) else None,
        )
