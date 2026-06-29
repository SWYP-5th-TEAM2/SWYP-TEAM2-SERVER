from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.room import CreateRoomRequest, JoinRoomRequest
from app.services.room import (
    create_room,
    get_my_rooms,
    get_room_detail,
    get_room_invite_code,
    join_room_by_invite_code,
    kick_room_member,
    leave_room,
)

router = APIRouter()

@router.post(
    "/",
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


@router.get(
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


@router.post(
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


@router.get(
    "/my",
    summary="가입된 방 목록 조회",
    description="현재 사용자가 가입한 방 목록을 조회합니다.",
)
def get_my_room_list(
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_my_rooms(
        db=db,
        user_id=user_id,
        keyword=keyword,
    )
    return success_response(
        data=response,
        message="가입된 방 정보 조회 성공",
    )


@router.get(
    "/{room_id}",
    summary="방 정보 조회",
    description="방 멤버가 방 정보와 멤버 목록을 조회합니다.",
)
def get_room(
    room_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_room_detail(
        db=db,
        user_id=user_id,
        room_id=room_id,
    )
    return success_response(
        data=response,
        message="방 정보 조회 성공",
    )


@router.delete(
    "/{room_id}/members/me",
    summary="방 나가기",
    description="현재 사용자의 RoomMember를 soft delete 처리합니다.",
)
def leave_my_room(
    room_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    leave_room(
        db=db,
        user_id=user_id,
        room_id=room_id,
    )
    return success_response(
        data=None,
        message="방 나가기 성공",
    )


@router.delete(
    "/{room_id}/members/{target_user_id}",
    summary="방 멤버 강퇴",
    description="HOST가 지정한 MEMBER를 soft delete 처리합니다.",
)
def kick_member(
    room_id: str,
    target_user_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    kick_room_member(
        db=db,
        requester_user_id=user_id,
        room_id=room_id,
        target_user_id=target_user_id,
    )
    return success_response(
        data=None,
        message="멤버 강퇴 성공",
    )
