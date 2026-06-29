from typing import Any

from pydantic import ConfigDict

from app.schemas.common import CamelModel


class CreateRoomRequest(CamelModel):
    room_name: Any = None
    room_color: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["roomName", "roomColor"],
            "properties": {
                "roomName": {
                    "type": "string",
                    "maxLength": 12,
                    "example": "현지네 덕질방",
                },
                "roomColor": {
                    "type": "string",
                    "pattern": "^#[0-9A-Fa-f]{6}$",
                    "example": "#1A2B3C",
                },
            },
        },
    )


class JoinRoomRequest(CamelModel):
    invite_code: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["inviteCode"],
            "properties": {
                "inviteCode": {
                    "type": "string",
                    "pattern": "^[A-Z0-9]{6}$",
                    "example": "A7K92B",
                },
            },
        },
    )
