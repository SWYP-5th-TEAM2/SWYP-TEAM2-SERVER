from pydantic import Field

from app.schemas.common import CamelModel


class SaveFcmTokenRequest(CamelModel):
    fcm_token: str | None = Field(
        min_length=1,
        default=None,
    )
    device_type: str | None = Field(
        min_length=1,
        default=None,
    )
