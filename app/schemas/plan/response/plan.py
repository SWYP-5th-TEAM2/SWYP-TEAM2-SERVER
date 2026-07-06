from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.common import CamelModel


class PlanUserPreviewResponse(CamelModel):
    user_id: UUID | None
    nickname: str | None
    profile_image_url: str | None = None


class PlanUserBasicResponse(CamelModel):
    user_id: UUID | None
    nickname: str | None


class PlanPlaceSummaryResponse(CamelModel):
    place_id: UUID | None
    title: str | None
    place_name: str | None
    address: str | None = None
    thumbnail_url: str | None = None


class PlanInvitationPlaceResponse(CamelModel):
    place_id: UUID | None
    title: str | None
    place_name: str | None
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
    requested_count: int
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
    recommended_response_deadline_at: datetime
    drawn_at: datetime
    target_member_count: int
    next_excluded_place_ids: list[UUID]
    remaining_drawable_place_count: int
    can_redraw: bool


class CreatePlanResponse(CamelModel):
    plan_id: UUID
    room_id: UUID
    plan_status: str
    scheduled_at: datetime
    response_deadline_at: datetime
    target_member_count: int
    target_members: list[PlanUserPreviewResponse]
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
    confirmed_at: datetime
    ticket: TicketResponse
    notification_created_count: int
    push_notification: PushNotificationSummaryResponse


class TicketLookupResponse(CamelModel):
    plan_id: UUID
    room_id: UUID | None
    confirmed_at: datetime
    ticket: TicketResponse


class PlanListSummaryResponse(CamelModel):
    total_count: int
    confirmed_count: int
    recruiting_count: int


class PlanListResponseSummaryResponse(CamelModel):
    responded_count: int
    total_target_count: int
    pending_count: int


class PlanListItemResponse(CamelModel):
    plan_id: UUID
    plan_status: str
    place: dict[str, Any]
    scheduled_at: datetime
    my_role: str
    entry_view_type: str
    response_summary: PlanListResponseSummaryResponse | None = None


class PlanListResponse(CamelModel):
    room_id: UUID
    status: str
    summary: PlanListSummaryResponse
    plans: list[dict[str, Any]]
    page_info: PlanPageInfoResponse


class InvitationResponse(CamelModel):
    plan_id: UUID
    room_id: UUID | None
    plan_status: str
    proposed_by: PlanUserBasicResponse
    place: PlanInvitationPlaceResponse
    scheduled_at: datetime
    response_deadline_at: datetime
    server_time: datetime
    response_summary: PlanResponseSummaryResponse
    members: list[PlanMemberResponse]
    my_response_status: str


class SavedPlanInfoResponse(CamelModel):
    plan_id: UUID
    scheduled_at: datetime


class SavePlanResponseResponse(CamelModel):
    plan: SavedPlanInfoResponse
    my_response: dict[str, object]
