from datetime import datetime
from uuid import UUID

from app.schemas.common import CamelModel


class PlanUserPreviewResponse(CamelModel):
    user_id: UUID | None
    nickname: str | None
    profile_image_url: str | None = None


class PlanPlaceSummaryResponse(CamelModel):
    place_id: UUID | None
    title: str | None
    place_name: str | None
    address: str | None = None
    thumbnail_url: str | None = None


class PlanPageInfoResponse(CamelModel):
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool


class PlanResponseSummaryResponse(CamelModel):
    going_count: int
    not_going_count: int
    pending_count: int
    total_target_count: int
    responded_count: int | None = None


class PushNotificationSummaryResponse(CamelModel):
    target_user_count: int
    requested_token_count: int
    sent_count: int
    failed_count: int
    push_status: str


class DrawSummaryResponse(CamelModel):
    room_id: UUID
    place_count: int


class PickedPlaceCreatorResponse(CamelModel):
    user_id: UUID | None
    nickname: str | None


class PickedPlaceResponse(CamelModel):
    place_id: UUID
    title: str
    place_name: str | None
    thumbnail_url: str | None
    created_by: PickedPlaceCreatorResponse


class DrawPlaceResponse(CamelModel):
    picked_place: PickedPlaceResponse
    recommended_scheduled_at: datetime
    drawn_at: datetime
    target_member_count: int


class CreatePlanResponse(CamelModel):
    plan_id: UUID
    room_id: UUID
    plan_status: str
    scheduled_at: datetime
    response_deadline_at: datetime
    target_member_count: int
    target_members: list[PlanUserPreviewResponse]
    remaining_target_member_count: int
    notification_created_count: int
    push_notification: PushNotificationSummaryResponse
    created_at: datetime


class PlanResponsesPlanResponse(CamelModel):
    plan_id: UUID
    status: str
    scheduled_at: datetime
    response_deadline_at: datetime


class PlanMemberResponse(CamelModel):
    user_id: UUID
    nickname: str | None
    profile_image_url: str | None
    response_status: str


class PlanResponsesResponse(CamelModel):
    server_time: datetime
    plan: PlanResponsesPlanResponse
    place: PlanPlaceSummaryResponse
    response_summary: PlanResponseSummaryResponse
    members: list[PlanMemberResponse]


class ReminderResponse(CamelModel):
    plan_id: UUID
    pending_count: int
    notification_created_count: int
    push_notification: PushNotificationSummaryResponse


class TicketResponse(CamelModel):
    ticket_id: str
    title: str | None
    address: str | None
    scheduled_at: datetime
    participant_count: int
    participants: list[PlanUserPreviewResponse]
    barcode_value: str
    share_url: str


class ClosePlanResponse(CamelModel):
    plan_id: UUID
    room_id: UUID | None
    plan_status: str
    confirmed_at: datetime
    ticket: TicketResponse
    notification_created_count: int
    push_notification: PushNotificationSummaryResponse


class PlanListSummaryResponse(CamelModel):
    total_count: int
    confirmed_count: int
    recruiting_count: int


class PlanListItemResponse(CamelModel):
    plan_id: UUID
    plan_status: str
    title: str | None
    place: PlanPlaceSummaryResponse
    scheduled_at: datetime
    response_deadline_at: datetime | None = None
    response_summary: PlanResponseSummaryResponse | None = None
    participant_count: int | None = None
    my_role: str
    my_response_status: str | None
    entry_view_type: str
    created_at: datetime
    confirmed_at: datetime | None = None


class PlanListResponse(CamelModel):
    server_time: datetime
    room_id: UUID
    status: str
    summary: PlanListSummaryResponse
    plans: list[PlanListItemResponse]
    page_info: PlanPageInfoResponse


class InvitationResponse(CamelModel):
    server_time: datetime
    actor: PlanUserPreviewResponse
    plan: PlanResponsesPlanResponse
    place: PlanPlaceSummaryResponse
    my_response_status: str
    response_summary: PlanResponseSummaryResponse
    going_members: list[PlanUserPreviewResponse]


class SavePlanResponseResponse(CamelModel):
    plan: PlanResponsesPlanResponse
    my_response: dict[str, object]
    response_summary: PlanResponseSummaryResponse
