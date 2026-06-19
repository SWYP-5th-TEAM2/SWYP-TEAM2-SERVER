from pydantic import Field

from app.schemas.common import CamelModel


class SocialLoginRequest(CamelModel):
    code: str = Field(
        min_length=1,
        description="소셜 로그인 인가 코드",
    )