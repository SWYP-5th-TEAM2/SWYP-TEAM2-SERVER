from uuid import UUID

from app.schemas.common import CamelModel


class PlaceCreatorResponse(CamelModel):
    user_id: UUID | None
    nickname: str | None


class PlacePageInfoResponse(CamelModel):
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool


class PlaceSummaryResponse(CamelModel):
    place_id: UUID
    title: str
    place_name: str | None
    address: str | None
    thumbnail_url: str | None
    created_by: PlaceCreatorResponse


class PlaceListResponse(CamelModel):
    room_id: UUID
    room_name: str
    place_count: int
    places: list[PlaceSummaryResponse]
    page_info: PlacePageInfoResponse


class PlaceDetailResponse(CamelModel):
    place_id: UUID
    room_id: UUID
    title: str
    place_name: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    thumbnail_url: str | None
    link_url: str | None
    image_url: str | None
    created_by: PlaceCreatorResponse


class CreatePlaceResponse(CamelModel):
    place_id: UUID
    room_id: UUID
    title: str
    place_name: str | None
    address: str | None
    thumbnail_url: str | None
    created_by: PlaceCreatorResponse


class UpdatePlaceResponse(CamelModel):
    place_id: UUID
    room_id: UUID
    title: str
    place_name: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    thumbnail_url: str | None
    link_url: str | None
    image_url: str | None
    updated_by: PlaceCreatorResponse


class DeletePlaceResponse(CamelModel):
    place_id: UUID
    remaining_place_count: int
