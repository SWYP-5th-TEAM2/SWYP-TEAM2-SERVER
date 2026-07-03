from uuid import UUID

from app.schemas.common import CamelModel


class ExtractedPlaceResponse(CamelModel):
    place_name: str | None
    address: str | None
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None


class PlaceImageExtractionResponse(CamelModel):
    extraction_id: UUID
    room_id: UUID
    image_url: str
    extracted_places: list[ExtractedPlaceResponse]
