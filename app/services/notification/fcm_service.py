from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import os
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ForbiddenException, UserNotFoundException
from app.models import DeviceType, NotificationType, User, UserFcmToken
from app.models.user.enums import UserAccountStatus
from app.repository.fcm import deactivate_fcm_tokens, find_active_fcm_token_rows
from app.schemas.notification import (
    FcmDiagnosticAcceptedTokenResponse,
    FcmDiagnosticActualSendSummaryResponse,
    FcmDiagnosticDryRunSummaryResponse,
    FcmDiagnosticFirebaseErrorResponse,
    FcmDiagnosticFirebaseResponse,
    FcmDiagnosticNotificationTypeResultResponse,
    FcmDiagnosticResponse,
    FcmDiagnosticTokenErrorResponse,
    FcmDiagnosticUserResponse,
)

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


_last_firebase_initialization_error_type: str | None = None
_last_firebase_initialization_error_message: str | None = None


def _set_firebase_initialization_error(exc: Exception | None) -> None:
    global _last_firebase_initialization_error_type
    global _last_firebase_initialization_error_message

    if exc is None:
        _last_firebase_initialization_error_type = None
        _last_firebase_initialization_error_message = None
        return

    _last_firebase_initialization_error_type = type(exc).__name__
    _last_firebase_initialization_error_message = str(exc)


def _get_messaging_module():
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError as exc:
        _set_firebase_initialization_error(exc)
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
        _set_firebase_initialization_error(None)
        return messaging
    except Exception as exc:
        _set_firebase_initialization_error(exc)
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

KST = timezone(timedelta(hours=9))
FCM_DIAGNOSTIC_TITLE = "FCM 실제 발송 진단"
FCM_DIAGNOSTIC_TYPE = "FCM_DIAGNOSTIC"

FIREBASE_STATUS_READY = "READY"
FIREBASE_STATUS_DISABLED = "DISABLED"
FIREBASE_STATUS_ERROR = "ERROR"

DRY_RUN_STATUS_VALIDATED = "VALIDATED"
DRY_RUN_STATUS_PARTIAL_FAILED = "PARTIAL_FAILED"
DRY_RUN_STATUS_FAILED = "FAILED"
DRY_RUN_STATUS_SKIPPED = "SKIPPED"

ACTUAL_SEND_STATUS_ACCEPTED = "ACCEPTED"
ACTUAL_SEND_STATUS_PARTIAL_FAILED = "PARTIAL_FAILED"
ACTUAL_SEND_STATUS_FAILED = "FAILED"
ACTUAL_SEND_STATUS_SKIPPED = "SKIPPED"

DIAGNOSTIC_STAGE_DRY_RUN = "DRY_RUN"
DIAGNOSTIC_STAGE_ACTUAL_SEND = "ACTUAL_SEND"

_NOTIFICATION_SETTING_BY_TYPE: dict[NotificationType, tuple[str | None, str | None]] = {
    NotificationType.PLAN_REQUESTED: ("candidate_place_enabled", "candidatePlaceEnabled"),
    NotificationType.RESPONSE_DEADLINE_SOON: ("vote_deadline_enabled", "voteDeadlineEnabled"),
    NotificationType.PLAN_CONFIRMED: ("schedule_confirmed_enabled", "scheduleConfirmedEnabled"),
    NotificationType.QUIET_RECOMMENDATION: (
        "quiet_recommendation_enabled",
        "quietRecommendationEnabled",
    ),
    # MEMBER_GOING은 현재 별도의 사용자 알림 설정 토글이 없다.
    NotificationType.MEMBER_GOING: (None, None),
}

_NOTIFICATION_SETTING_DISABLED_REASON: dict[NotificationType, str] = {
    NotificationType.PLAN_REQUESTED: "CANDIDATE_PLACE_NOTIFICATION_DISABLED",
    NotificationType.RESPONSE_DEADLINE_SOON: "VOTE_DEADLINE_NOTIFICATION_DISABLED",
    NotificationType.PLAN_CONFIRMED: "SCHEDULE_CONFIRMED_NOTIFICATION_DISABLED",
    NotificationType.QUIET_RECOMMENDATION: "QUIET_RECOMMENDATION_NOTIFICATION_DISABLED",
}


def _enum_value(value) -> str:
    return getattr(value, "value", str(value))


def _extract_error_code(exc: Exception) -> str | None:
    code = getattr(exc, "code", None)
    if code is None:
        code = getattr(exc, "status_code", None)
    if code is None:
        return None
    return _enum_value(code)


def _notification_setting_state(
    *,
    user: User,
    notification_type: NotificationType,
) -> tuple[str | None, bool]:
    model_field, response_field = _NOTIFICATION_SETTING_BY_TYPE[notification_type]
    enabled = bool(getattr(user, model_field)) if model_field is not None else True
    return response_field, enabled


def _build_diagnostic_message(
    messaging,
    *,
    token: str,
    device_type: DeviceType,
    request_id: UUID,
    target_user_id: UUID,
    notification_type: NotificationType,
    send_mode: str,
):
    payload = FcmPushPayload(
        user_id=target_user_id,
        notification_id=request_id,
        notification_type=notification_type,
        target_type=FCM_DIAGNOSTIC_TYPE,
        target_id=target_user_id,
        title=f"{FCM_DIAGNOSTIC_TITLE} ({notification_type.value})",
        body=f"{notification_type.value} 알림 유형의 진단 테스트입니다.",
    )
    return messaging.Message(
        token=token,
        notification=messaging.Notification(
            title=payload.title,
            body=payload.body,
        ),
        data={
            "type": FCM_DIAGNOSTIC_TYPE,
            "diagnosticRequestId": str(request_id),
            "targetUserId": str(target_user_id),
            "notificationType": notification_type.value,
            "sendMode": send_mode,
            "deviceType": device_type.value,
        },
        android=_build_android_config(messaging, payload=payload),
        apns=_build_apns_config(messaging, payload=payload),
    )


def _firebase_credentials_source() -> str:
    if settings.firebase_credentials_path:
        return "FIREBASE_CREDENTIALS_PATH"
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return "GOOGLE_APPLICATION_CREDENTIALS"
    return "APPLICATION_DEFAULT_CREDENTIALS"


def _build_firebase_diagnostic_response(messaging) -> FcmDiagnosticFirebaseResponse:
    project_id = settings.firebase_project_id
    credential_type = None

    try:
        import firebase_admin

        app = firebase_admin.get_app("[DEFAULT]")
        project_id = getattr(app, "project_id", None) or project_id
        credential = getattr(app, "_credential", None) or getattr(app, "credential", None)
        credential_type = type(credential).__name__ if credential is not None else None
    except Exception:
        # 초기화 실패 원인은 _get_messaging_module()에서 별도로 기록한다.
        pass

    if not settings.firebase_push_enabled:
        status = FIREBASE_STATUS_DISABLED
    elif messaging is None:
        status = FIREBASE_STATUS_ERROR
    else:
        status = FIREBASE_STATUS_READY

    error = None
    if _last_firebase_initialization_error_type or _last_firebase_initialization_error_message:
        error = FcmDiagnosticFirebaseErrorResponse(
            type=_last_firebase_initialization_error_type or "FirebaseInitializationError",
            message=(
                _last_firebase_initialization_error_message
                or "Firebase messaging module is unavailable."
            ),
        )

    return FcmDiagnosticFirebaseResponse(
        status=status,
        project_id=project_id,
        credential_source=_firebase_credentials_source(),
        credential_type=credential_type,
        error=error,
    )


def _dry_run_summary_status(*, validated_count: int, failed_count: int) -> str:
    if validated_count > 0 and failed_count == 0:
        return DRY_RUN_STATUS_VALIDATED
    if validated_count > 0 and failed_count > 0:
        return DRY_RUN_STATUS_PARTIAL_FAILED
    if failed_count > 0:
        return DRY_RUN_STATUS_FAILED
    return DRY_RUN_STATUS_SKIPPED


def _actual_send_summary_status(*, accepted_count: int, failed_count: int) -> str:
    if accepted_count > 0 and failed_count == 0:
        return ACTUAL_SEND_STATUS_ACCEPTED
    if accepted_count > 0 and failed_count > 0:
        return ACTUAL_SEND_STATUS_PARTIAL_FAILED
    if failed_count > 0:
        return ACTUAL_SEND_STATUS_FAILED
    return ACTUAL_SEND_STATUS_SKIPPED


def _ensure_diagnostic_requester(
    db: Session,
    *,
    requester_user_id: UUID,
) -> None:
    """인증된 ACTIVE 사용자인지만 확인한다.

    FCM 진단 API는 target userId와 요청자 userId의 일치 여부나 ADMIN 권한을
    검사하지 않는다. 따라서 로그인된 ACTIVE 사용자는 모든 사용자를 진단할 수 있다.
    """
    requester = db.execute(
        select(User).where(
            User.id == requester_user_id,
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if requester is None:
        raise UserNotFoundException()
    if requester.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()


def _type_level_skip_reason(
    *,
    user: User,
    token_rows: list[UserFcmToken],
    notification_type: NotificationType,
    messaging_available: bool,
) -> str | None:
    if user.status != UserAccountStatus.ACTIVE:
        return "USER_NOT_ACTIVE"

    _, setting_enabled = _notification_setting_state(
        user=user,
        notification_type=notification_type,
    )
    if not setting_enabled:
        return _NOTIFICATION_SETTING_DISABLED_REASON[notification_type]

    if not token_rows:
        return "NO_FCM_TOKEN"
    if not any(token_row.is_active for token_row in token_rows):
        return "NO_ACTIVE_FCM_TOKEN"
    if not settings.firebase_push_enabled:
        return "FIREBASE_PUSH_DISABLED"
    if not messaging_available:
        return "FIREBASE_MESSAGING_UNAVAILABLE"
    return None


def _token_error(
    *,
    stage: str,
    token_row: UserFcmToken,
    exc: Exception,
) -> FcmDiagnosticTokenErrorResponse:
    return FcmDiagnosticTokenErrorResponse(
        stage=stage,
        masked_token=_mask_token(token_row.fcm_token),
        device_type=_enum_value(token_row.device_type),
        error_code=_extract_error_code(exc),
        error_type=type(exc).__name__,
        error_message=str(exc),
    )


def _diagnose_fcm_notification_type(
    *,
    target_user: User,
    token_rows: list[UserFcmToken],
    messaging,
    request_id: UUID,
    target_user_id: UUID,
    notification_type: NotificationType,
    send_actual: bool,
) -> FcmDiagnosticNotificationTypeResultResponse:
    setting_field, setting_enabled = _notification_setting_state(
        user=target_user,
        notification_type=notification_type,
    )
    active_token_rows = [token_row for token_row in token_rows if token_row.is_active]
    type_skip_reason = _type_level_skip_reason(
        user=target_user,
        token_rows=token_rows,
        notification_type=notification_type,
        messaging_available=messaging is not None,
    )
    eligible_token_count = len(active_token_rows) if type_skip_reason is None else 0

    errors: list[FcmDiagnosticTokenErrorResponse] = []
    dry_run_validated_token_ids: set[UUID] = set()
    dry_run_attempted_count = 0
    dry_run_failed_count = 0

    if active_token_rows and messaging is None:
        initialization_exc = RuntimeError(
            _last_firebase_initialization_error_message
            or "Firebase messaging module is unavailable."
        )
        dry_run_failed_count = len(active_token_rows)
        errors.extend(
            _token_error(
                stage=DIAGNOSTIC_STAGE_DRY_RUN,
                token_row=token_row,
                exc=initialization_exc,
            )
            for token_row in active_token_rows
        )
    elif messaging is not None:
        for token_row in active_token_rows:
            dry_run_attempted_count += 1
            try:
                dry_run_message = _build_diagnostic_message(
                    messaging,
                    token=token_row.fcm_token,
                    device_type=token_row.device_type,
                    request_id=request_id,
                    target_user_id=target_user_id,
                    notification_type=notification_type,
                    send_mode="DRY_RUN",
                )
                messaging.send(dry_run_message, dry_run=True)
                dry_run_validated_token_ids.add(token_row.id)
            except Exception as exc:
                dry_run_failed_count += 1
                errors.append(
                    _token_error(
                        stage=DIAGNOSTIC_STAGE_DRY_RUN,
                        token_row=token_row,
                        exc=exc,
                    )
                )

    dry_run = FcmDiagnosticDryRunSummaryResponse(
        status=_dry_run_summary_status(
            validated_count=len(dry_run_validated_token_ids),
            failed_count=dry_run_failed_count,
        ),
        attempted_token_count=dry_run_attempted_count,
        validated_count=len(dry_run_validated_token_ids),
        failed_count=dry_run_failed_count,
    )

    actual_send = None
    if send_actual:
        actual_attempted_count = 0
        accepted_count = 0
        actual_failed_count = 0
        accepted_tokens: list[FcmDiagnosticAcceptedTokenResponse] = []
        actual_skip_reason = type_skip_reason

        if actual_skip_reason is None:
            for token_row in active_token_rows:
                if token_row.id not in dry_run_validated_token_ids:
                    continue

                actual_attempted_count += 1
                try:
                    actual_message = _build_diagnostic_message(
                        messaging,
                        token=token_row.fcm_token,
                        device_type=token_row.device_type,
                        request_id=request_id,
                        target_user_id=target_user_id,
                        notification_type=notification_type,
                        send_mode="ACTUAL",
                    )
                    message_id = messaging.send(actual_message)
                    accepted_count += 1
                    accepted_tokens.append(
                        FcmDiagnosticAcceptedTokenResponse(
                            masked_token=_mask_token(token_row.fcm_token),
                            message_id=message_id,
                        )
                    )
                except Exception as exc:
                    actual_failed_count += 1
                    errors.append(
                        _token_error(
                            stage=DIAGNOSTIC_STAGE_ACTUAL_SEND,
                            token_row=token_row,
                            exc=exc,
                        )
                    )
                    logger.warning(
                        "FCM diagnostic actual send failed. requestId=%s targetUserId=%s notificationType=%s deviceType=%s token=%s error=%s",
                        request_id,
                        target_user_id,
                        notification_type.value,
                        _enum_value(token_row.device_type),
                        _mask_token(token_row.fcm_token),
                        exc,
                    )

            if actual_attempted_count == 0:
                actual_skip_reason = "DRY_RUN_FAILED"

        actual_send = FcmDiagnosticActualSendSummaryResponse(
            status=_actual_send_summary_status(
                accepted_count=accepted_count,
                failed_count=actual_failed_count,
            ),
            attempted_token_count=actual_attempted_count,
            accepted_count=accepted_count,
            failed_count=actual_failed_count,
            device_delivery_confirmed=False,
            skipped_reason=actual_skip_reason,
            accepted_tokens=accepted_tokens or None,
        )

    return FcmDiagnosticNotificationTypeResultResponse(
        notification_type=notification_type.value,
        setting_field=setting_field,
        setting_enabled=setting_enabled,
        eligible_token_count=eligible_token_count,
        dry_run=dry_run,
        actual_send=actual_send,
        errors=errors or None,
    )


def diagnose_fcm_push_for_user(
    db: Session,
    *,
    requester_user_id: UUID,
    target_user_id: UUID,
    requested_notification_type: str,
    notification_types: list[NotificationType],
    send_actual: bool,
) -> FcmDiagnosticResponse:
    """사용자 FCM 상태를 알림 타입별로 간결하게 진단한다.

    notificationType=ALL인 경우 모든 NotificationType을 순서대로 진단한다.
    정상 결과는 요약하고 token별 실패 상세는 errors에만 포함한다.
    sendActual=true이면 dry-run 검증을 통과하고 실제 발송 조건까지 만족한 token에만
    타입별 테스트 push를 전송한다. 진단 과정에서는 DB 데이터를 변경하지 않는다.
    """
    target_user = db.execute(
        select(User).where(
            User.id == target_user_id,
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if target_user is None:
        raise UserNotFoundException()

    _ensure_diagnostic_requester(
        db,
        requester_user_id=requester_user_id,
    )

    token_rows = list(
        db.execute(
            select(UserFcmToken)
            .where(
                UserFcmToken.user_id == target_user_id,
                UserFcmToken.deleted_at.is_(None),
            )
            .order_by(UserFcmToken.updated_at.desc())
        ).scalars().all()
    )

    request_id = uuid4()
    attempted_at = datetime.now(KST)
    messaging = _get_messaging_module()
    firebase_response = _build_firebase_diagnostic_response(messaging)

    notification_type_results = [
        _diagnose_fcm_notification_type(
            target_user=target_user,
            token_rows=token_rows,
            messaging=messaging,
            request_id=request_id,
            target_user_id=target_user_id,
            notification_type=notification_type,
            send_actual=send_actual,
        )
        for notification_type in notification_types
    ]

    logger.info(
        "FCM diagnostic completed. requestId=%s requesterUserId=%s targetUserId=%s requestedNotificationType=%s selectedTypes=%s sendActual=%s tokens=%s",
        request_id,
        requester_user_id,
        target_user_id,
        requested_notification_type,
        [notification_type.value for notification_type in notification_types],
        send_actual,
        len(token_rows),
    )

    return FcmDiagnosticResponse(
        request_id=request_id,
        attempted_at=attempted_at,
        notification_type=requested_notification_type,
        send_actual=send_actual,
        target_user=FcmDiagnosticUserResponse(
            user_id=target_user.id,
            nickname=target_user.nickname,
            user_status=_enum_value(target_user.status),
            total_fcm_token_count=len(token_rows),
            active_fcm_token_count=sum(1 for token_row in token_rows if token_row.is_active),
        ),
        firebase=firebase_response,
        notification_type_results=notification_type_results,
    )
