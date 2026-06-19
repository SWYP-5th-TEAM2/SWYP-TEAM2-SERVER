from app.services.auth.oauth.base import OAuthClient, OAuthUserInfo


class AppleOAuthClient(OAuthClient):
    async def get_access_token(self, code: str) -> str:
        pass

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        pass