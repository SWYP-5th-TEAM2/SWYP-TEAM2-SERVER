from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.place import CreatePlaceRequest, UpdatePlaceRequest
from app.services.place import (
    create_place,
    delete_place,
    get_place_detail,
    get_places,
    update_place,
)

router = APIRouter()


@router.get(
    "",
    summary="장소 후보 목록 조회",
    description="후보함에서 방에 저장된 장소 후보 목록을 조회합니다.",
)
def get_place_list(
    room_id: str | None = Query(
        default=None,
        alias="roomId",
        description="후보함을 조회할 방 ID",
    ),
    keyword: str | None = Query(default=None, description="장소 후보 검색어"),
    page: str | None = Query(default="0", description="페이지 번호"),
    size: str | None = Query(default="20", description="한 페이지당 조회 개수"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_places(
        db=db,
        user_id=user_id,
        room_id=room_id,
        keyword=keyword,
        page=page,
        size=size,
    )
    return success_response(
        data=response,
        message="후보함 조회 성공",
    )


@router.post(
    "",
    summary="장소 후보 생성",
    description="S8 확인 화면에서 맞아요 뽑기함에 넣기 버튼을 눌렀을 때 호출합니다.",
)
def create_new_place(
    request: CreatePlaceRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = create_place(
        db=db,
        user_id=user_id,
        request=request,
    )
    return success_response(
        data=response,
        message="장소 후보 생성 성공",
    )


@router.get(
    "/{place_id}",
    summary="장소 상세 정보 조회",
    description="장소 후보 상세 화면에 필요한 정보를 조회합니다.",
)
def get_place(
    place_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_place_detail(
        db=db,
        user_id=user_id,
        place_id=place_id,
    )
    return success_response(
        data=response,
        message="장소 상세 정보 조회 성공",
    )


@router.patch(
    "/{place_id}",
    summary="장소 후보 수정",
    description="장소 후보 수정 화면에서 수정완료 버튼을 눌렀을 때 호출합니다.",
)
def update_place_info(
    place_id: str,
    request: UpdatePlaceRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = update_place(
        db=db,
        user_id=user_id,
        place_id=place_id,
        request=request,
    )
    return success_response(
        data=response,
        message="장소 후보 수정 성공",
    )


@router.delete(
    "/{place_id}",
    summary="장소 후보 삭제",
    description="후보함 또는 장소 상세 화면에서 장소 후보를 삭제합니다.",
)
def delete_place_info(
    place_id: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = delete_place(
        db=db,
        user_id=user_id,
        place_id=place_id,
    )
    return success_response(
        data=response,
        message="장소 후보 삭제 성공",
    )
