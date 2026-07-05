from __future__ import annotations

from dataclasses import dataclass
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import DeviceType, NotificationType
from app.repository.fcm import deactivate_fcm_tokens, find_active_fcm_token_rows

logger = logging.getLogger(__name__)

PUSH_STATUS_REQUESTED = "REQUESTED"
PUSH_STATUS_PARTIAL_FAILED = "PARTIAL_FAILED"
PUSH_STATUS_FAILED = "FAILED"
PUSH_STATUS_SKIPPED = "SKIPPED"

ANDROID_FCM_PRIORITY_HIGH = "high"
APNS_PUSH_TYPE_ALERT = "alert"
APNS_PRIORITY_IMMEDIATE = "10"
APNS_SOUND_DEFAULT = "default"


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
    # 토큰 자체가 만료/삭제/오염된 경우에만 비활성화한다.
    # "invalid-argument" 같은 포괄적인 오류는 메시지 구성 또는 Firebase 프로젝트 설정 문제일 수 있으므로
    # 여기서 바로 토큰을 비활성화하지 않는다.
    invalid_keywords = (
        "registration-token-not-registered",
        "unregistered",
        "invalid registration token",
        "invalid-registration-token",
        "requested entity was not found",
    )
    return any(keyword in text for keyword in invalid_keywords)


def _mask_token(token: str) -> str:
    if len(token) <= 16:
        return "***"
    return f"{token[:8]}...{token[-6:]}"


def _get_messaging_module():
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError:
        logger.exception("firebase-admin package is not installed")
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
        logger.exception("Failed to initialize Firebase Admin SDK")
        return None


def _build_android_config(messaging, *, payload: FcmPushPayload):
    """Android notification 옵션.

    title/body는 top-level notification에도 넣고 AndroidNotification에도 넣는다.
    이렇게 하면 토큰에 저장된 deviceType이 잘못 들어간 경우에도 기본 알림 렌더링이 깨질 가능성을 줄일 수 있다.
    """
    return messaging.AndroidConfig(
        priority=ANDROID_FCM_PRIORITY_HIGH,
        notification=messaging.AndroidNotification(
            title=payload.title,
            body=payload.body,
        ),
    )


def _build_apns_config(messaging, *, payload: FcmPushPayload):
    """iOS/APNs alert push 옵션."""
    return messaging.APNSConfig(
        headers={
            "apns-push-type": APNS_PUSH_TYPE_ALERT,
            "apns-priority": APNS_PRIORITY_IMMEDIATE,
        },
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                alert=messaging.ApsAlert(
                    title=payload.title,
                    body=payload.body,
                ),
                sound=APNS_SOUND_DEFAULT,
            ),
        ),
    )


def _build_fcm_message(
    messaging,
    *,
    token: str,
    device_type: DeviceType,
    payload: FcmPushPayload,
):
    """Build a platform-safe FCM message.

    기존 구현은 deviceType에 따라 AndroidConfig 또는 APNSConfig 중 하나만 넣었다.
    그런데 앱에서 deviceType이 잘못 저장되었거나 iOS/Android 연동 중 토큰 정보가 꼬이면
    반대 플랫폼 토큰에 표시용 payload가 충분히 전달되지 않을 수 있다.

    FCM은 토큰 플랫폼에 맞는 설정만 사용하므로, top-level notification과 Android/APNs 설정을 함께 넣어
    Android/iOS 모두 같은 서버 payload로 받을 수 있게 한다.
    """
    data = _build_data(payload)
    data["deviceType"] = device_type.value

    return messaging.Message(
        token=token,
        notification=messaging.Notification(
            title=payload.title,
            body=payload.body,
        ),
        data=data,
        android=_build_android_config(messaging, payload=payload),
        apns=_build_apns_config(messaging, payload=payload),
    )


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
        logger.info(
            "FCM push skipped: no active tokens or notification setting disabled. targetUsers=%s notificationType=%s",
            len(target_user_ids),
            payloads[0].notification_type.value if payloads else None,
        )
        return FcmDispatchResult(
            target_user_count=len(target_user_ids),
            requested_token_count=0,
            sent_count=0,
            failed_count=0,
            push_status=PUSH_STATUS_SKIPPED,
        )

    if not settings.firebase_push_enabled:
        logger.info(
            "FCM push skipped: FIREBASE_PUSH_ENABLED=false. targetUsers=%s tokens=%s",
            len(target_user_ids),
            len(token_rows),
        )
        return FcmDispatchResult(
            target_user_count=len(target_user_ids),
            requested_token_count=len(token_rows),
            sent_count=0,
            failed_count=0,
            push_status=PUSH_STATUS_SKIPPED,
        )

    messaging = _get_messaging_module()
    if messaging is None:
        logger.error(
            "FCM push failed: Firebase messaging module is unavailable. targetUsers=%s tokens=%s",
            len(target_user_ids),
            len(token_rows),
        )
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

    for user_id, token, device_type in token_rows:
        payload = payload_by_user_id.get(user_id)
        if payload is None:
            continue
        try:
            message = _build_fcm_message(
                messaging,
                token=token,
                device_type=device_type,
                payload=payload,
            )
            messaging.send(message)
            sent_count += 1
        except Exception as exc:  # FCM 실패는 API 실패로 전파하지 않음
            failed_count += 1
            logger.warning(
                "FCM send failed. userId=%s deviceType=%s token=%s error=%s",
                user_id,
                device_type.value if hasattr(device_type, "value") else device_type,
                _mask_token(token),
                exc,
            )
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
