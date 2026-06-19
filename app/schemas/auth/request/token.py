from pydantic import BaseModel, Field


class ReissueRequest(BaseModel):
    refresh_token: str = Field(
        alias="refreshToken",
        min_length=1,
        description="Refresh Token",
    )

class LogoutRequest(BaseModel):
    refresh_token: str = Field(
        alias="refreshToken",
        min_length=1,
        description="Refresh Token",
    )