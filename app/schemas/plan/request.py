from typing import Any

from pydantic import ConfigDict

from app.schemas.common import CamelModel


class DrawPlaceRequest(CamelModel):
    room_id: Any = None
    previous_place_id: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["roomId"],
            "properties": {
                "roomId": {"type": "string", "example": "string_room_id"},
                "previousPlaceId": {
                    "type": "string",
                    "nullable": True,
                    "example": "string_place_id",
                },
            },
        },
    )


class CreatePlanRequest(CamelModel):
    room_id: Any = None
    place_id: Any = None
    scheduled_at: Any = None
    response_deadline_at: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["roomId", "placeId", "scheduledAt", "responseDeadlineAt"],
            "properties": {
                "roomId": {"type": "string", "example": "string_room_id"},
                "placeId": {"type": "string", "example": "string_place_id"},
                "scheduledAt": {
                    "type": "string",
                    "format": "date-time",
                    "example": "2026-06-20T14:00:00+09:00",
                },
                "responseDeadlineAt": {
                    "type": "string",
                    "format": "date-time",
                    "example": "2026-06-19T21:00:00+09:00",
                },
            },
        },
    )


class SavePlanResponseRequest(CamelModel):
    response_status: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["responseStatus"],
            "properties": {
                "responseStatus": {
                    "type": "string",
                    "example": "GOING",
                    "enum": ["GOING", "NOT_GOING"],
                }
            },
        },
    )
