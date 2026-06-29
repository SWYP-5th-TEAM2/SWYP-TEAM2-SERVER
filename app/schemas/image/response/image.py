from uuid import UUID

from app.schemas.common import CamelModel


class ImageUploadResponse(CamelModel):
    image_id: UUID
    image_url: str