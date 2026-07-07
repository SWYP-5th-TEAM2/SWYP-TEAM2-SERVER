from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.common import CamelModel


class NotificationPageInfoResponse(CamelModel):
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool


class NotificationListResponse(CamelModel):
    server_time: datetime
    notifications: list[dict[str, Any]]
    page_info: NotificationPageInfoResponse


class NotificationUserBasicResponse(CamelModel):
    user_id: UUID | None
    nickname: str | None


class NotificationUserPreviewResponse(CamelModel):
    user_id: UUID | None
    nickname: str | None
    profile_image_url: str | None = None


class NotificationInvitationPlaceResponse(CamelModel):
    place_id: UUID | None
    title: str | None
    place_name: str | None
    thumbnail_url: str | None = None


class NotificationResponseSummaryResponse(CamelModel):
    going_count: int
    not_going_count: int
    pending_count: int
    total_target_count: int
    responded_count: int


class NotificationMemberResponse(CamelModel):
    user_id: UUID
    nickname: str | None
    profile_image_url: str | None
    response_status: str


class NotificationVoteScreenResponse(CamelModel):
    notification_id: UUID
    plan_id: UUID
    room_id: UUID | None
    plan_status: str
    proposed_by: NotificationUserBasicResponse
    place: NotificationInvitationPlaceResponse
    scheduled_at: datetime
    response_deadline_at: datetime
    server_time: datetime
    response_summary: NotificationResponseSummaryResponse
    members: list[NotificationMemberResponse]
    my_response_status: str


class NotificationReadResponse(CamelModel):
    notification_id: UUID
    is_read: bool


class NotificationReadAllResponse(CamelModel):
    read_count: int
