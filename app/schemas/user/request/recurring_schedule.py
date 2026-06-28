from typing import Any

from pydantic import ConfigDict, Field

from app.schemas.common import CamelModel


class CreateRecurringScheduleRequest(CamelModel):
    title: str = Field(
        min_length=1,
    )
    days_of_week: list[str] = Field(
        min_length=1,
    )
    start_time: str
    end_time: str

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["title", "dayOfWeek", "startTime", "endTime"],
        },
    )


class UpdateRecurringScheduleRequest(CamelModel):
    title: str | None = None
    days_of_week: list[str] | None = None
    start_time: str | None = None
    end_time: str | None = None


class UpdateRecurringScheduleActivationRequest(CamelModel):
    is_active: Any = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["isActive"],
            "properties": {
                "isActive": {"type": "boolean"},
            },
        },
    )
