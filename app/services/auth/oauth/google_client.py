import httpx

from app.config import settings
from app.core.exceptions import SocialLoginFailedException, RequiredUserInfoMissingException
from app.models.user.enums import Provider
from app.services.auth.oauth.base import OAuthClient, OAuthUserInfo

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_HTTP_TIMEOUT = 5.0

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

