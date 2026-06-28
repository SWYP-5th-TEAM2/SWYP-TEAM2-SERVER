from pydantic import Field

from app.schemas.common import CamelModel


class SaveFcmTokenRequest(CamelModel):
    fcm_token: str = Field(
        min_length=1,
    )
    device_type: str = Field(
        min_length=1,
    )
