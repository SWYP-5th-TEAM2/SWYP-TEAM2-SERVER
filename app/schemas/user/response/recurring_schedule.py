from uuid import UUID

from app.schemas.common import CamelModel


class RecurringScheduleResponse(CamelModel):
    recurring_schedule_group_id: UUID
    title: str
    days_of_week: list[str]
    start_time: str
    end_time: str
    is_active: bool


class RecurringScheduleListResponse(CamelModel):
    recurring_schedules: list[RecurringScheduleResponse]


class RecurringScheduleMutationResponse(CamelModel):
    recurring_schedule_id: UUID


class RecurringScheduleActivationResponse(CamelModel):
    recurring_schedule_id: UUID
    is_active: bool
