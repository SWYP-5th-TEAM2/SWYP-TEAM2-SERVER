import logging
import re
from html import unescape

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
NAVER_PROVIDER = "NAVER"
SUPPORTED_PROVIDERS = {KAKAO_PROVIDER, NAVER_PROVIDER}

KAKAO_LOCAL_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
NAVER_LOCAL_SEARCH_URL = "https://openapi.naver.com/v1/search/local.json"

HTTP_TIMEOUT = 5.0

MAX_KEYWORD_LENGTH = 50
DEFAULT_PAGE = 1
DEFAULT_SIZE = 10
MIN_PAGE = 1
MAX_PAGE = 45
MIN_SIZE = 1
MAX_SIZE = 15
NAVER_MAX_SIZE = 5

# 현재 서비스는 국내 장소 검색을 전제로 한다.
KOREA_MIN_LATITUDE = 33.0
KOREA_MAX_LATITUDE = 39.5
KOREA_MIN_LONGITUDE = 124.0
KOREA_MAX_LONGITUDE = 132.0


def _validate_keyword(keyword: str | None) -> str:
    if keyword is None or not keyword.strip():
        raise PlaceSearchKeywordMissingException()

    normalized_keyword = keyword.strip()
    if len(normalized_keyword) > MAX_KEYWORD_LENGTH:
        raise PlaceSearchKeywordTooLongException()

    return normalized_keyword


def _validate_provider(provider: str | None) -> str:
    normalized_provider = (provider or KAKAO_PROVIDER).strip().upper()
    if normalized_provider not in SUPPORTED_PROVIDERS:
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
    # Kakao Local API는 OAuth Client ID가 아니라 REST API Key가 필요합니다.
    # OAuth용 KAKAO_CLIENT_ID를 fallback으로 사용하면 운영 환경에서 401/502성 오류를 만들 수 있어
    # 장소 검색은 KAKAO_LOCAL_REST_API_KEY만 사용하도록 분리합니다.
    api_key = settings.kakao_local_rest_api_key
    if not api_key or api_key.strip() == "kakao-local-rest-api-key":
        logger.error("KAKAO_LOCAL_REST_API_KEY is not configured for place search.")
        raise ExternalPlaceSearchServiceUnavailableException()

    return api_key.strip()


def _get_naver_local_credentials() -> tuple[str, str]:
    client_id = settings.naver_local_client_id
    client_secret = settings.naver_local_client_secret

    if (
        not client_id
        or not client_secret
        or client_id.strip() == "naver-local-client-id"
        or client_secret.strip() == "naver-local-client-secret"
    ):
        logger.error("NAVER_LOCAL_CLIENT_ID or NAVER_LOCAL_CLIENT_SECRET is not configured for place search.")
        raise ExternalPlaceSearchServiceUnavailableException()

    return client_id.strip(), client_secret.strip()


def _parse_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_valid_latitude(value: float | None) -> bool:
    return value is not None and -90 <= value <= 90


def _is_valid_longitude(value: float | None) -> bool:
    return value is not None and -180 <= value <= 180


def _is_korea_latitude(value: float | None) -> bool:
    return value is not None and KOREA_MIN_LATITUDE <= value <= KOREA_MAX_LATITUDE


def _is_korea_longitude(value: float | None) -> bool:
    return value is not None and KOREA_MIN_LONGITUDE <= value <= KOREA_MAX_LONGITUDE


def _normalize_naver_coordinate(value: object, *, axis: str) -> float | None:
    """Normalize Naver local search coordinate values.

    Naver local search returns integer mapx/mapy values. In current local search
    responses these values are commonly WGS84 coordinates scaled by 10,000,000.
    If a future response already provides decimal degrees, keep that value.
    """

    parsed_value = _parse_float(value)
    if parsed_value is None:
        return None

    if axis == "longitude" and _is_korea_longitude(parsed_value):
        return parsed_value
    if axis == "latitude" and _is_korea_latitude(parsed_value):
        return parsed_value

    scaled_value = parsed_value / 10_000_000
    if axis == "longitude" and _is_korea_longitude(scaled_value):
        return scaled_value
    if axis == "latitude" and _is_korea_latitude(scaled_value):
        return scaled_value

    return None


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    return unescape(re.sub(r"<[^>]+>", "", value)).strip()


def _build_place_search_result(
    *,
    provider: str,
    place_name: str | None,
    address: str | None,
    latitude: float | None,
    longitude: float | None,
) -> PlaceSearchResult | None:
    if not place_name or not _is_valid_latitude(latitude) or not _is_valid_longitude(longitude):
        return None

    return PlaceSearchResult(
        provider=provider,
        place_name=place_name,
        address=address or "",
        latitude=latitude,
        longitude=longitude,
    )


async def _search_places_by_kakao(
    *,
    keyword: str,
    page: int,
    size: int,
) -> PlaceSearchResponse:
    api_key = _get_kakao_rest_api_key()

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
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
        logger.warning("Kakao place search rate limited: status=%s body=%s", response.status_code, response.text[:500])
        raise PlaceSearchRateLimitExceededException()

    if 500 <= response.status_code:
        logger.warning("Kakao place search service unavailable: status=%s body=%s", response.status_code, response.text[:500])
        raise ExternalPlaceSearchServiceUnavailableException()

    if response.status_code != 200:
        logger.warning("Kakao place search API failed: status=%s body=%s", response.status_code, response.text[:500])
        raise ExternalPlaceSearchApiFailedException()

    try:
        body = response.json()
    except ValueError as exc:
        raise ExternalPlaceSearchApiFailedException() from exc

    documents = body.get("documents") or []
    meta = body.get("meta") or {}

    search_results: list[PlaceSearchResult] = []
    for document in documents:
        result = _build_place_search_result(
            provider=KAKAO_PROVIDER,
            place_name=document.get("place_name"),
            address=document.get("road_address_name") or document.get("address_name"),
            latitude=_parse_float(document.get("y")),
            longitude=_parse_float(document.get("x")),
        )

        if result is None:
            logger.warning(
                "Skip invalid Kakao place search document: %s",
                document,
            )
            continue

        search_results.append(result)

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


async def _search_places_by_naver(
    *,
    keyword: str,
    page: int,
    size: int,
) -> PlaceSearchResponse:
    client_id, client_secret = _get_naver_local_credentials()
    display_size = min(size, NAVER_MAX_SIZE)

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(
                NAVER_LOCAL_SEARCH_URL,
                params={
                    "query": keyword,
                    "display": display_size,
                    # Naver Local Search API start parameter is fixed to 1.
                    "start": 1,
                    "sort": "random",
                },
                headers={
                    "X-Naver-Client-Id": client_id,
                    "X-Naver-Client-Secret": client_secret,
                },
            )
    except httpx.TimeoutException as exc:
        raise ExternalPlaceSearchServiceUnavailableException() from exc
    except httpx.HTTPError as exc:
        raise ExternalPlaceSearchApiFailedException() from exc

    if response.status_code == 429:
        logger.warning("Naver place search rate limited: status=%s body=%s", response.status_code, response.text[:500])
        raise PlaceSearchRateLimitExceededException()

    if 500 <= response.status_code:
        logger.warning("Naver place search service unavailable: status=%s body=%s", response.status_code, response.text[:500])
        raise ExternalPlaceSearchServiceUnavailableException()

    if response.status_code != 200:
        logger.warning("Naver place search API failed: status=%s body=%s", response.status_code, response.text[:500])
        raise ExternalPlaceSearchApiFailedException()

    try:
        body = response.json()
    except ValueError as exc:
        raise ExternalPlaceSearchApiFailedException() from exc

    items = body.get("items") or []

    search_results: list[PlaceSearchResult] = []
    for item in items:
        result = _build_place_search_result(
            provider=NAVER_PROVIDER,
            place_name=_strip_html(item.get("title")),
            address=item.get("roadAddress") or item.get("address"),
            latitude=_normalize_naver_coordinate(item.get("mapy"), axis="latitude"),
            longitude=_normalize_naver_coordinate(item.get("mapx"), axis="longitude"),
        )

        if result is None:
            logger.warning(
                "Skip invalid Naver place search item: %s",
                item,
            )
            continue

        search_results.append(result)

    total_count = body.get("total")
    if not isinstance(total_count, int):
        total_count = len(search_results)

    return PlaceSearchResponse(
        provider=NAVER_PROVIDER,
        keyword=keyword,
        search_results=search_results,
        page_info=PlaceSearchPageInfo(
            page=page,
            size=display_size,
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
        if normalized_provider == NAVER_PROVIDER:
            return await _search_places_by_naver(
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
