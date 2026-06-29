from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.room import CreateRoomRequest, JoinRoomRequest
from app.services.room import (
    create_room,
    get_room_invite_code,
    join_room_by_invite_code,
)

room_router = APIRouter(
    prefix="/rooms",
    tags=["Room"],
)


@room_router.post(
    "",
    summary="방 생성",
    description="방을 생성하고 로그인한 사용자를 HOST로 등록합니다.",
)
def create_new_room(
    request: CreateRoomRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = create_room(
        db=db,
        user_id=user_id,
        request=request,
    )
    return success_response(
        data=response,
        message="방 생성 성공",
    )


@room_router.get(
    "/{room_id}/invite-code",
    summary="초대 코드 조회",
    description="방 멤버가 해당 방의 초대 코드를 조회합니다.",
)
def get_invite_code(
    room_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_room_invite_code(
        db=db,
        user_id=user_id,
        room_id=room_id,
    )
    return success_response(
        data=response,
        message="초대 코드 조회 성공",
    )


@room_router.post(
    "/join",
    summary="초대 코드로 방 가입",
    description="초대 코드에 해당하는 방에 MEMBER로 가입합니다.",
)
def join_room(
    request: JoinRoomRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = join_room_by_invite_code(
        db=db,
        user_id=user_id,
        request=request,
    )
    return success_response(
        data=response,
        message="초대코드로 방 가입 성공",
    )
