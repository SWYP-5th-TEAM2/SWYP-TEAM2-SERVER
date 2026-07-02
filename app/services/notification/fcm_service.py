from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import NotificationType
from app.repository.fcm import deactivate_fcm_tokens, find_active_fcm_token_rows

PUSH_STATUS_REQUESTED = "REQUESTED"
PUSH_STATUS_PARTIAL_FAILED = "PARTIAL_FAILED"
PUSH_STATUS_FAILED = "FAILED"
PUSH_STATUS_SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class FcmPushPayload:
    user_id: UUID
    notification_id: UUID
    notification_type: NotificationType
    target_type: str | None
    target_id: UUID | None
    title: str
    body: str


@dataclass(frozen=True)
class FcmDispatchResult:
    target_user_count: int
    requested_token_count: int
    sent_count: int
    failed_count: int
    push_status: str


def _build_data(payload: FcmPushPayload) -> dict[str, str]:
    data = {
        "notificationId": str(payload.notification_id),
        "type": payload.notification_type.value,
    }
    if payload.target_type is not None:
        data["targetType"] = payload.target_type
    if payload.target_id is not None:
        data["targetId"] = str(payload.target_id)
    return data


def _is_invalid_token_error(exc: Exception) -> bool:
    text = str(exc).lower()
    invalid_keywords = (
        "registration-token-not-registered",
        "unregistered",
        "invalid registration token",
        "invalid-argument",
        "requested entity was not found",
    )
    return any(keyword in text for keyword in invalid_keywords)


def _get_messaging_module():
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError:
        return None

    try:
        app_name = "[DEFAULT]"
        try:
            firebase_admin.get_app(app_name)
        except ValueError:
            options = {}
            if settings.firebase_project_id:
                options["projectId"] = settings.firebase_project_id

            if settings.firebase_credentials_path:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred, options=options or None, name=app_name)
            else:
                # GOOGLE_APPLICATION_CREDENTIALS 또는 실행 환경의 기본 credential 사용
                firebase_admin.initialize_app(options=options or None, name=app_name)
        return messaging
    except Exception:
        return None


def dispatch_fcm_push_notifications(
    db: Session,
    *,
    payloads: list[FcmPushPayload],
) -> FcmDispatchResult:
    """Send FCM push notifications best-effort.

    인앱 알림 생성과 핵심 도메인 처리는 이미 완료된 뒤 호출되는 부가 처리다.
    FCM 발송 실패는 plan API 자체를 실패시키지 않고 결과 요약으로만 반환한다.
    """
    target_user_ids = list({payload.user_id for payload in payloads})
    if not target_user_ids:
        return FcmDispatchResult(
            target_user_count=0,
            requested_token_count=0,
            sent_count=0,
            failed_count=0,
            push_status=PUSH_STATUS_SKIPPED,
        )

    token_rows = find_active_fcm_token_rows(
        db=db,
        user_ids=target_user_ids,
        notification_type=payloads[0].notification_type if payloads else None,
    )
    if not token_rows:
        return FcmDispatchResult(
            target_user_count=len(target_user_ids),
            requested_token_count=0,
            sent_count=0,
            failed_count=0,
            push_status=PUSH_STATUS_SKIPPED,
        )

    if not settings.firebase_push_enabled:
        return FcmDispatchResult(
            target_user_count=len(target_user_ids),
            requested_token_count=len(token_rows),
            sent_count=0,
            failed_count=0,
            push_status=PUSH_STATUS_SKIPPED,
        )

    messaging = _get_messaging_module()
    if messaging is None:
        return FcmDispatchResult(
            target_user_count=len(target_user_ids),
            requested_token_count=len(token_rows),
            sent_count=0,
            failed_count=len(token_rows),
            push_status=PUSH_STATUS_FAILED,
        )

    payload_by_user_id = {payload.user_id: payload for payload in payloads}
    sent_count = 0
    failed_count = 0
    invalid_tokens: list[str] = []

    for user_id, token in token_rows:
        payload = payload_by_user_id.get(user_id)
        if payload is None:
            continue
        try:
            message = messaging.Message(
                token=token,
                notification=messaging.Notification(
                    title=payload.title,
                    body=payload.body,
                ),
                data=_build_data(payload),
            )
            messaging.send(message)
            sent_count += 1
        except Exception as exc:  # FCM 실패는 API 실패로 전파하지 않음
            failed_count += 1
            if _is_invalid_token_error(exc):
                invalid_tokens.append(token)

    if invalid_tokens:
        deactivate_fcm_tokens(db=db, fcm_tokens=invalid_tokens)
        db.commit()

    if sent_count > 0 and failed_count == 0:
        push_status = PUSH_STATUS_REQUESTED
    elif sent_count > 0 and failed_count > 0:
        push_status = PUSH_STATUS_PARTIAL_FAILED
    elif sent_count == 0 and failed_count > 0:
        push_status = PUSH_STATUS_FAILED
    else:
        push_status = PUSH_STATUS_SKIPPED

    return FcmDispatchResult(
        target_user_count=len(target_user_ids),
        requested_token_count=len(token_rows),
        sent_count=sent_count,
        failed_count=failed_count,
        push_status=push_status,
    )
