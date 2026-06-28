from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import unquote

from app.core.exceptions import SocialLoginFailedException
from app.models.user.enums import Provider


@dataclass(frozen=True)
class OAuthUserInfo:
    provider: Provider
    provider_id: str
    email: str | None = None
    nickname: str | None = None

class OAuthClient(ABC):
    @abstractmethod
    async def get_access_token(self, code: str) -> str:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        pass

    async def authenticate(self, code: str) -> OAuthUserInfo:
        normalized_code = unquote(code).strip()
        access_token = await self.get_access_token(normalized_code)
        return await self.get_user_info(access_token)

    async def authenticate_token(
        self,
        token: str,
        code: str | None = None,
    ) -> OAuthUserInfo:
        normalized_token = token.strip()
        if not normalized_token:
            raise SocialLoginFailedException()

        return await self.get_user_info(normalized_token)
