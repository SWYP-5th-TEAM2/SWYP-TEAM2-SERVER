import httpx

from app.config import settings
from app.core.exceptions import SocialLoginFailedException
from app.models.user.enums import Provider
from app.services.auth.oauth.base import OAuthClient, OAuthUserInfo

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"
KAKAO_HTTP_TIMEOUT = 5.0

class KakaoOAuthClient(OAuthClient):
    async def get_access_token(self, code: str) -> str:
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.kakao_client_id,
            "redirect_uri": settings.kakao_redirect_uri,
            "code": code,
        }

        if settings.kakao_client_secret:
            data["client_secret"] = settings.kakao_client_secret

        try:
            async with httpx.AsyncClient(timeout=KAKAO_HTTP_TIMEOUT) as client:
                response = await client.post(
                    url=KAKAO_TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
                )
        except httpx.HTTPError:
            raise SocialLoginFailedException()

        if response.status_code != 200:
            raise SocialLoginFailedException()

        body = response.json()
        access_token = body.get("access_token")

        if not isinstance(access_token, str) or not access_token:
            raise SocialLoginFailedException()

        return access_token


    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        try:
            async with httpx.AsyncClient(timeout=KAKAO_HTTP_TIMEOUT) as client:
                response = await client.get(
                    url=KAKAO_USER_INFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.HTTPError:
            raise SocialLoginFailedException()

        if response.status_code != 200:
            raise SocialLoginFailedException()

        body = response.json()

        provider_id = body.get("id")
        kakao_account = body.get("kakao_account") or {}
        properties = body.get("properties") or {}
        profile = kakao_account.get("profile") or {}

        email = kakao_account.get("email")
        nickname = (properties.get("nickname") or profile.get("nickname"))

        if provider_id is None:
            raise SocialLoginFailedException()

        return OAuthUserInfo(
            provider=Provider.KAKAO,
            provider_id=str(provider_id),
            email=email,
            nickname=nickname,
        )