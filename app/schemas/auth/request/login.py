from pydantic import Field

from app.schemas.common import CamelModel


class SocialLoginRequest(CamelModel):
    provider: str = Field(
        min_length=1,
        description="소셜 로그인 제공자(KAKAO, GOOGLE, APPLE)",
    )
    token: str = Field(
        min_length=1,
        description="Kakao access token / Google ID token / Apple identity token",
    )
    code: str | None = Field(
        default=None,
        description="Apple authorization code",
    )
