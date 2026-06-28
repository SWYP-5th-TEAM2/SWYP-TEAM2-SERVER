from uuid import UUID

from app.schemas.common import CamelModel


class SaveFcmTokenResponse(CamelModel):
    fcm_token_id: UUID
