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


class FcmDiagnosticUserResponse(CamelModel):
    user_id: UUID
    nickname: str | None
    user_status: str
    total_fcm_token_count: int
    active_fcm_token_count: int


class FcmDiagnosticFirebaseErrorResponse(CamelModel):
    type: str
    message: str


class FcmDiagnosticFirebaseResponse(CamelModel):
    status: str
    project_id: str | None
    credential_source: str
    credential_type: str | None = None
    error: FcmDiagnosticFirebaseErrorResponse | None = None


class FcmDiagnosticDryRunSummaryResponse(CamelModel):
    status: str
    attempted_token_count: int
    validated_count: int
    failed_count: int


class FcmDiagnosticAcceptedTokenResponse(CamelModel):
    masked_token: str
    message_id: str


class FcmDiagnosticActualSendSummaryResponse(CamelModel):
    status: str
    attempted_token_count: int
    accepted_count: int
    failed_count: int
    device_delivery_confirmed: bool = False
    skipped_reason: str | None = None
    accepted_tokens: list[FcmDiagnosticAcceptedTokenResponse] | None = None


class FcmDiagnosticTokenErrorResponse(CamelModel):
    stage: str
    masked_token: str
    device_type: str
    error_code: str | None = None
    error_type: str
    error_message: str


class FcmDiagnosticNotificationTypeResultResponse(CamelModel):
    notification_type: str
    setting_field: str | None = None
    setting_enabled: bool
    eligible_token_count: int
    dry_run: FcmDiagnosticDryRunSummaryResponse
    actual_send: FcmDiagnosticActualSendSummaryResponse | None = None
    errors: list[FcmDiagnosticTokenErrorResponse] | None = None


class FcmDiagnosticResponse(CamelModel):
    request_id: UUID
    attempted_at: datetime
    notification_type: str
    send_actual: bool
    target_user: FcmDiagnosticUserResponse
    firebase: FcmDiagnosticFirebaseResponse
    notification_type_results: list[FcmDiagnosticNotificationTypeResultResponse]


class NotificationReadResponse(CamelModel):
    notification_id: UUID
    is_read: bool


class NotificationReadAllResponse(CamelModel):
    read_count: int
