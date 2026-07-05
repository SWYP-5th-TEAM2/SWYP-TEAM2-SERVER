from typing import Any

from pydantic import ConfigDict

from app.schemas.common import CamelModel


class DrawPlaceRequest(CamelModel):
    room_id: Any = None
    excluded_place_ids: list[Any] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["roomId"],
            "properties": {
                "roomId": {"type": "string", "example": "string_room_id"},
                "excludedPlaceIds": {
                    "type": "array",
                    "items": {"type": "string"},
                    "nullable": True,
                    "example": ["string_place_id_1", "string_place_id_2"],
                    "description": "현재 뽑기 화면에서 이미 나왔던 장소 후보 ID 목록",
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
                    "description": "장소 후보 뽑기 API에서 받은 recommendedResponseDeadlineAt 값을 전달합니다.",
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


class ReminderTestRequest(CamelModel):
    target_user_id: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["targetUserId"],
            "properties": {
                "targetUserId": {
                    "type": "string",
                    "example": "string_user_id",
                    "description": "테스트 알림을 보낼 미응답 대상 사용자 ID",
                }
            },
        },
    )
