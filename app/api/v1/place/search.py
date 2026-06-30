from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.services.place import search_places

router = APIRouter()


@router.get(
    "/search",
    summary="장소 검색",
    description="S7-1-A에서 키워드로 장소를 검색할 때 호출합니다.",
)
async def search_place(
    keyword: str | None = Query(default=None, description="장소 검색어"),
    provider: str | None = Query(default="KAKAO", description="장소 검색 제공자"),
    page: str | None = Query(default="1", description="검색 결과 페이지 번호"),
    size: str | None = Query(default="10", description="한 번에 조회할 검색 결과 개수"),
    user_id: UUID = Depends(get_current_user_id),
):
    response = await search_places(
        keyword=keyword,
        provider=provider,
        page=page,
        size=size,
    )

    return success_response(
        data=response,
        message="장소 검색 성공",
    )
