from typing import Any

from pydantic import ConfigDict

from app.schemas.common import CamelModel


class UpdateNotificationSettingsRequest(CamelModel):
    candidate_place_enabled: Any = None
    vote_deadline_enabled: Any = None
    schedule_confirmed_enabled: Any = None
    quiet_recommendation_enabled: Any = None

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "additionalProperties": False,
            "properties": {
                "candidatePlaceEnabled": {"type": "boolean"},
                "voteDeadlineEnabled": {"type": "boolean"},
                "scheduleConfirmedEnabled": {"type": "boolean"},
                "quietRecommendationEnabled": {"type": "boolean"},
            },
        },
    )
