from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.services.notification import (
    get_notification_list,
    get_notification_vote_screen,
    read_all_notifications,
    read_notification,
)

router = APIRouter()


@router.get(
    "",
    summary="알림 목록 조회",
    description="S13 알림 탭에서 사용자에게 도착한 알림 목록을 조회합니다.",
)
def get_notifications(
    page: str | None = Query(default="0", description="페이지 번호"),
    size: str | None = Query(default="20", description="한 페이지당 조회 개수"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_notification_list(db=db, user_id=user_id, page=page, size=size)
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
