from pydantic import Field

from app.schemas.common import CamelModel


class ReissueRequest(CamelModel):
    refresh_token: str = Field(
        min_length=1,
        description="Refresh Token",
    )

class LogoutRequest(CamelModel):
    refresh_token: str = Field(
        min_length=1,
        description="Refresh Token",
    )