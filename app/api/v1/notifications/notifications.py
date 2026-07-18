from uuid import UUID
from enum import Enum

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.models import NotificationType
from app.services.notification import (
    diagnose_fcm_push_for_user,
    get_notification_list,
    get_notification_vote_screen,
    read_all_notifications,
    read_notification,
)

router = APIRouter()


class FcmDiagnosticNotificationType(str, Enum):
    ALL = "ALL"
    PLAN_REQUESTED = NotificationType.PLAN_REQUESTED.value
    PLAN_CONFIRMED = NotificationType.PLAN_CONFIRMED.value
    MEMBER_GOING = NotificationType.MEMBER_GOING.value
    QUIET_RECOMMENDATION = NotificationType.QUIET_RECOMMENDATION.value
    RESPONSE_DEADLINE_SOON = NotificationType.RESPONSE_DEADLINE_SOON.value


@router.post(
    "/fcm-diagnostics/users/{userId}",
    summary="FCM 사용자 발송 진단",
    description=(
        "로그인된 ACTIVE 사용자가 특정 사용자의 FCM token, 전체 알림 설정, Firebase 초기화 상태를 조회하고 "
        "실제 알림을 보내지 않는 dry-run 검증을 수행합니다. "
        "notificationType=ALL이면 모든 알림 타입을 한 번에 진단합니다. "
        "sendActual=true이면 dry-run을 통과하고 실제 발송 조건도 만족한 token에 테스트 push를 전송합니다. "
        "정상 결과는 요약하고 실패한 token의 오류 정보만 상세하게 반환합니다. "
    ),
)
def diagnose_user_fcm_push(
    target_user_id: UUID = Path(alias="userId", description="FCM 발송을 진단할 사용자 ID"),
    notification_type: FcmDiagnosticNotificationType = Query(
        default=FcmDiagnosticNotificationType.RESPONSE_DEADLINE_SOON,
        alias="notificationType",
        description="진단할 알림 타입. ALL이면 모든 알림 타입을 한 번에 진단",
    ),
    send_actual: bool = Query(
        default=False,
        alias="sendActual",
        description="true이면 dry-run 통과 token에 실제 테스트 push를 발송",
    ),
    db: Session = Depends(get_db),
    requester_user_id: UUID = Depends(get_current_user_id),
):
    selected_notification_types = (
        [
            NotificationType(item.value)
            for item in FcmDiagnosticNotificationType
            if item != FcmDiagnosticNotificationType.ALL
        ]
        if notification_type == FcmDiagnosticNotificationType.ALL
        else [NotificationType(notification_type.value)]
    )
    response = diagnose_fcm_push_for_user(
        db=db,
        requester_user_id=requester_user_id,
        target_user_id=target_user_id,
        requested_notification_type=notification_type.value,
        notification_types=selected_notification_types,
        send_actual=send_actual,
    )
    return success_response(
        data=response.model_dump(by_alias=True, exclude_none=True),
        message="FCM 사용자 발송 진단 성공",
    )


@router.get(
    "/",
    summary="알림 목록 조회",
    description="S13 알림 탭에서 사용자에게 도착한 알림 목록을 조회합니다.",
)
def get_notifications(
    room_id: str | None = Query(default=None, alias="roomId", description="알림 목록을 조회할 방 ID"),
    page: str | None = Query(default="0", description="페이지 번호"),
    size: str | None = Query(default="20", description="한 페이지당 조회 개수"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_notification_list(db=db, user_id=user_id, room_id=room_id, page=page, size=size)
    return success_response(data=response, message="알림 목록 조회 성공")


@router.get(
    "/{notification_id}/votes",
    summary="알림 기반 약속 응답 화면 조회",
    description="S13 알림 목록에서 약속 제안 알림을 눌렀을 때 S14-1 또는 S14-3 화면에 필요한 정보를 조회합니다.",
)
def get_notification_votes(
    notification_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_notification_vote_screen(db=db, user_id=user_id, notification_id=notification_id)
    return success_response(data=response, message="알림 기반 약속 응답 화면 조회 성공")


@router.patch(
    "/{notification_id}/read",
    summary="알림 읽음 처리",
    description="S13 알림 목록에서 특정 알림을 눌렀을 때 해당 알림을 읽음 처리합니다.",
)
def read_one_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = read_notification(db=db, user_id=user_id, notification_id=notification_id)
    return success_response(data=response, message="알림 읽음 처리 성공")


@router.patch(
    "/read-all",
    summary="알림 전체 읽음 처리",
    description="S13 알림 화면에서 모두 읽기 버튼을 눌렀을 때 현재 사용자의 읽지 않은 알림을 모두 읽음 처리합니다.",
)
def read_all_user_notifications(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = read_all_notifications(db=db, user_id=user_id)
    return success_response(data=response, message="알림 전체 읽음 처리 성공")
