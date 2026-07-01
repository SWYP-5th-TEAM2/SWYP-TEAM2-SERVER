from typing import Any

from pydantic import ConfigDict

from app.schemas.common import CamelModel


class CreatePlaceRequest(CamelModel):
    room_id: Any = None
    title: Any = None
    place_name: Any = None
    address: Any = None
    latitude: Any = None
    longitude: Any = None
    thumbnail_url: Any = None
    link_url: Any = None
    image_url: Any = None
    source_type: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["roomId", "title"],
            "properties": {
                "roomId": {"type": "string", "example": "string_room_id"},
                "title": {"type": "string", "example": "덕질 성지 한정 포토존"},
                "placeName": {"type": "string", "example": "매머드 커피 정릉점"},
                "address": {"type": "string", "example": "서울 성북구 정릉로 77"},
                "latitude": {"type": "number", "example": 37.602123},
                "longitude": {"type": "number", "example": 127.013456},
                "thumbnailUrl": {
                    "type": "string",
                    "example": "https://example.com/place-thumbnail.png",
                },
                "linkUrl": {
                    "type": "string",
                    "example": "https://www.instagram.com/example",
                },
                "imageUrl": {
                    "type": "string",
                    "nullable": True,
                    "example": "https://example.com/place-image.png",
                },
                "sourceType": {
                    "type": "string",
                    "example": "DIRECT_SEARCH",
                },
            },
        },
    )


class UpdatePlaceRequest(CamelModel):
    title: Any = None
    place_name: Any = None
    address: Any = None
    latitude: Any = None
    longitude: Any = None
    thumbnail_url: Any = None
    link_url: Any = None
    image_url: Any = None
    source_type: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "properties": {
                "title": {"type": "string", "example": "덕질 성지 한정 포토존"},
                "placeName": {"type": "string", "example": "매머드 커피 정릉점"},
                "address": {"type": "string", "example": "서울 성북구 정릉로 77"},
                "latitude": {"type": "number", "example": 37.602123},
                "longitude": {"type": "number", "example": 127.013456},
                "thumbnailUrl": {
                    "type": "string",
                    "example": "https://example.com/place-thumbnail.png",
                },
                "linkUrl": {
                    "type": "string",
                    "example": "https://www.instagram.com/example",
                },
                "imageUrl": {
                    "type": "string",
                    "nullable": True,
                    "example": "https://example.com/place-image.png",
                },
                "sourceType": {
                    "type": "string",
                    "example": "DIRECT_SEARCH",
                },
            },
        },
    )
