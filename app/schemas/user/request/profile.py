from pydantic import ConfigDict, Field

from app.schemas.common import CamelModel


class UpdateUserProfileRequest(CamelModel):
    nickname: str = Field(
        min_length=1,
    )
    profile_image_url: str | None = None

    model_config = ConfigDict(
        json_schema_extra={"required": ["nickname"]},
    )
