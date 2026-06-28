from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.user import (
    CreateRecurringScheduleRequest,
    UpdateRecurringScheduleRequest,
)
from app.services.user import (
    create_recurring_schedule,
    delete_recurring_schedule,
    get_recurring_schedules,
    update_recurring_schedule,
)

router = APIRouter(
    prefix="/me/recurring-schedules",
)


@router.get(
    "",
    summary="반복 일정 조회",
    description="로그인한 사용자가 등록한 반복 일정 목록을 조회합니다."
)
def get_my_recurring_schedules(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_recurring_schedules(
        db=db,
        user_id=user_id,
    )
    return success_response(
        data=response,
        message="반복 일정 조회 성공",
    )


@router.post(
    "",
    summary="반복 일정 등록",
    description="로그인한 사용자의 반복 일정을 등록합니다."
)
def create_my_recurring_schedule(
    request: CreateRecurringScheduleRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = create_recurring_schedule(
        db=db,
        user_id=user_id,
        request=request,
    )
    return success_response(
        data=response,
        message="반복 일정 등록 성공",
    )


@router.patch(
    "/{recurring_schedule_id}",
    summary="반복 일정 수정",
    description="로그인한 사용자가 등록한 반복 일정의 내용을 수정합니다."
)
def update_my_recurring_schedule(
    recurring_schedule_id: str,
    request: UpdateRecurringScheduleRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = update_recurring_schedule(
        db=db,
        user_id=user_id,
        recurring_schedule_id=recurring_schedule_id,
        request=request,
    )
    return success_response(
        data=response,
        message="반복 일정 수정 성공",
    )


@router.delete(
    "/{recurring_schedule_id}",
    summary="반복 일정 삭제",
    description="로그인한 사용자가 등록한 반복 일정을 삭제합니다."
)
def delete_my_recurring_schedule(
    recurring_schedule_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    delete_recurring_schedule(
        db=db,
        user_id=user_id,
        recurring_schedule_id=recurring_schedule_id,
    )
    return success_response(
        data=None,
        message="반복 일정 삭제 성공",
    )
