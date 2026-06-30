import logging

import httpx

from app.config import settings
from app.core.exceptions import (
    ExternalPlaceSearchApiFailedException,
    ExternalPlaceSearchServiceUnavailableException,
    PlaceSearchFailedException,
    PlaceSearchKeywordMissingException,
    PlaceSearchKeywordTooLongException,
    PlaceSearchPageRequestInvalidException,
    PlaceSearchRateLimitExceededException,
    UnsupportedPlaceSearchProviderException,
)
from app.schemas.place import (
    PlaceSearchPageInfo,
    PlaceSearchResponse,
    PlaceSearchResult,
)

logger = logging.getLogger(__name__)

KAKAO_PROVIDER = "KAKAO"
KAKAO_LOCAL_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_HTTP_TIMEOUT = 5.0

MAX_KEYWORD_LENGTH = 50
DEFAULT_PAGE = 1
DEFAULT_SIZE = 10
MIN_PAGE = 1
MAX_PAGE = 45
MIN_SIZE = 1
MAX_SIZE = 15


def _validate_keyword(keyword: str | None) -> str:
    if keyword is None or not keyword.strip():
        raise PlaceSearchKeywordMissingException()

    normalized_keyword = keyword.strip()
    if len(normalized_keyword) > MAX_KEYWORD_LENGTH:
        raise PlaceSearchKeywordTooLongException()

    return normalized_keyword


def _validate_provider(provider: str | None) -> str:
    normalized_provider = (provider or KAKAO_PROVIDER).strip().upper()
    if normalized_provider != KAKAO_PROVIDER:
        raise UnsupportedPlaceSearchProviderException()

    return normalized_provider


def _parse_positive_int(
    value: str | None,
    *,
    default: int,
    min_value: int,
    max_value: int,
) -> int:
    if value is None or not str(value).strip():
        return default

    try:
        parsed_value = int(str(value).strip())
    except (TypeError, ValueError):
        raise PlaceSearchPageRequestInvalidException()

    if parsed_value < min_value or parsed_value > max_value:
        raise PlaceSearchPageRequestInvalidException()

    return parsed_value


def _get_kakao_rest_api_key() -> str:
    # 장소 검색 API는 Kakao Local REST API Key를 우선 사용한다.
    # 기존 OAuth용 KAKAO_CLIENT_ID에 REST API Key를 넣어둔 환경도 고려해 fallback을 둔다.
    api_key = settings.kakao_local_rest_api_key or settings.kakao_client_id
    if not api_key or api_key.strip() in {
        "kakao-local-rest-api-key",
        "kakao-client-id",
    }:
        raise ExternalPlaceSearchApiFailedException()

    return api_key.strip()


def _parse_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


async def _search_places_by_kakao(
    *,
    keyword: str,
    page: int,
    size: int,
) -> PlaceSearchResponse:
    api_key = _get_kakao_rest_api_key()

    try:
        async with httpx.AsyncClient(timeout=KAKAO_HTTP_TIMEOUT) as client:
            response = await client.get(
                KAKAO_LOCAL_SEARCH_URL,
                params={
                    "query": keyword,
                    "page": page,
                    "size": size,
                },
                headers={
                    "Authorization": f"KakaoAK {api_key}",
                },
            )
    except httpx.TimeoutException as exc:
        raise ExternalPlaceSearchServiceUnavailableException() from exc
    except httpx.HTTPError as exc:
        raise ExternalPlaceSearchApiFailedException() from exc

    if response.status_code == 429:
        raise PlaceSearchRateLimitExceededException()

    if 500 <= response.status_code:
        raise ExternalPlaceSearchServiceUnavailableException()

    if response.status_code != 200:
        raise ExternalPlaceSearchApiFailedException()

    try:
        body = response.json()
    except ValueError as exc:
        raise ExternalPlaceSearchApiFailedException() from exc

    documents = body.get("documents") or []
    meta = body.get("meta") or {}

    search_results: list[PlaceSearchResult] = []
    for document in documents:
        latitude = _parse_float(document.get("y"))
        longitude = _parse_float(document.get("x"))
        place_name = document.get("place_name")

        if not place_name or latitude is None or longitude is None:
            logger.warning(
                "Skip invalid Kakao place search document: %s",
                document,
            )
            continue

        address = (
            document.get("road_address_name")
            or document.get("address_name")
            or ""
        )

        search_results.append(
            PlaceSearchResult(
                provider=KAKAO_PROVIDER,
                place_name=place_name,
                address=address,
                latitude=latitude,
                longitude=longitude,
            )
        )

    total_count = meta.get("total_count")
    if not isinstance(total_count, int):
        total_count = len(search_results)

    return PlaceSearchResponse(
        provider=KAKAO_PROVIDER,
        keyword=keyword,
        search_results=search_results,
        page_info=PlaceSearchPageInfo(
            page=page,
            size=size,
            total_count=total_count,
        ),
    )


async def search_places(
    *,
    keyword: str | None,
    provider: str | None,
    page: str | None,
    size: str | None,
) -> PlaceSearchResponse:
    normalized_keyword = _validate_keyword(keyword)
    normalized_provider = _validate_provider(provider)
    parsed_page = _parse_positive_int(
        page,
        default=DEFAULT_PAGE,
        min_value=MIN_PAGE,
        max_value=MAX_PAGE,
    )
    parsed_size = _parse_positive_int(
        size,
        default=DEFAULT_SIZE,
        min_value=MIN_SIZE,
        max_value=MAX_SIZE,
    )

    try:
        if normalized_provider == KAKAO_PROVIDER:
            return await _search_places_by_kakao(
                keyword=normalized_keyword,
                page=parsed_page,
                size=parsed_size,
            )
    except (
        PlaceSearchKeywordMissingException,
        PlaceSearchKeywordTooLongException,
        UnsupportedPlaceSearchProviderException,
        PlaceSearchPageRequestInvalidException,
        PlaceSearchRateLimitExceededException,
        ExternalPlaceSearchApiFailedException,
        ExternalPlaceSearchServiceUnavailableException,
    ):
        raise
    except Exception as exc:
        raise PlaceSearchFailedException() from exc

    raise UnsupportedPlaceSearchProviderException()
