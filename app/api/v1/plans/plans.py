from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.plan import CreatePlanRequest, DrawPlaceRequest, SavePlanResponseRequest
from app.services.plan import (
    close_plan,
    create_plan,
    draw_place,
    get_draw_summary,
    get_invitation,
    get_plan_list,
    get_plan_responses,
    get_ticket,
    save_plan_response,
    send_pending_reminders,
)

router = APIRouter()


@router.get(
    "/draws/summary",
    summary="뽑기 화면 정보 조회",
    description="딸깍 화면에서 후보함에 모인 장소 후보 수를 조회합니다.",
)
def get_plan_draw_summary(
    room_id: str | None = Query(default=None, alias="roomId", description="뽑기 정보를 조회할 방 ID"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_draw_summary(db=db, user_id=user_id, room_id=room_id)
    return success_response(data=response, message="뽑기 화면 정보 조회 성공")


@router.post(
    "/draw",
    summary="장소 후보 뽑기",
    description="딸깍 화면에서 뽑기 버튼을 눌렀을 때 장소 후보와 추천 약속 시간을 반환합니다.",
)
def draw_plan_place(
    request: DrawPlaceRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = draw_place(db=db, user_id=user_id, request=request)
    return success_response(data=response, message="장소 후보 뽑기 성공")


@router.get(
    "",
    summary="약속 목록 조회",
    description="약속 탭에서 전체, 확정, 모집중 약속 목록을 조회합니다.",
)
def get_plans(
    room_id: str | None = Query(default=None, alias="roomId", description="약속 목록을 조회할 방 ID"),
    status: str | None = Query(default="ALL", description="약속 상태 필터"),
    page: str | None = Query(default="0", description="페이지 번호"),
    size: str | None = Query(default="20", description="한 페이지당 조회 개수"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_plan_list(
        db=db,
        user_id=user_id,
        room_id=room_id,
        status=status,
        page=page,
        size=size,
    )
    return success_response(data=response, message="약속 목록 조회 성공")


@router.post(
    "",
    summary="약속 제안 생성",
    description="S11-1에서 N명에게 물어보기 버튼을 눌렀을 때 호출합니다.",
)
def create_new_plan(
    request: CreatePlanRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = create_plan(db=db, user_id=user_id, request=request)
    return success_response(data=response, message="약속 제안 생성 성공")


@router.get(
    "/{plan_id}/responses",
    summary="응답 현황 조회",
    description="S12에서 약속 제안의 멤버별 응답 현황을 조회합니다.",
)
def get_responses(
    plan_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_plan_responses(db=db, user_id=user_id, plan_id=plan_id)
    return success_response(data=response, message="응답 현황 조회 성공")


@router.post(
    "/{plan_id}/reminders",
    summary="미응답자 알림 발송",
    description="S12에서 답 안 한 친구 콕 찌르기 버튼을 눌렀을 때 호출합니다.",
)
def send_reminders(
    plan_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = send_pending_reminders(db=db, user_id=user_id, plan_id=plan_id)
    return success_response(data=response, message="미응답자 알림 발송 성공")


@router.post(
    "/{plan_id}/close",
    summary="응답 마감",
    description="S12에서 지금 마감하기 버튼을 눌렀을 때 호출합니다.",
)
def close_plan_responses(
    plan_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = close_plan(db=db, user_id=user_id, plan_id=plan_id)
    return success_response(data=response, message="응답 마감 성공")


@router.get(
    "/{plan_id}/invitation",
    summary="약속 기반 약속 응답 화면 조회",
    description="S15-1 약속 목록에서 모집중 약속 카드를 눌렀을 때 S14-1 또는 S14-3 화면에 필요한 정보를 조회합니다.",
)
def get_plan_invitation(
    plan_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_invitation(db=db, user_id=user_id, plan_id=plan_id)
    return success_response(data=response, message="약속 응답 화면 조회 성공")


@router.put(
    "/{plan_id}/response",
    summary="갈래/못 가 응답 저장",
    description="S14-1 또는 S14-3에서 갈래/이번엔 못 가 버튼을 눌렀을 때 호출합니다.",
)
def save_response(
    plan_id: str,
    request: SavePlanResponseRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = save_plan_response(db=db, user_id=user_id, plan_id=plan_id, request=request)
    return success_response(data=response, message="응답 저장 성공")


@router.get(
    "/{plan_id}/ticket",
    summary="약속 티켓 조회",
    description="확정된 약속의 티켓 화면 데이터를 조회합니다.",
)
def get_plan_ticket(
    plan_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_ticket(db=db, user_id=user_id, plan_id=plan_id)
    return success_response(data=response, message="약속 티켓 조회 성공")
