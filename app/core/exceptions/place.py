from http import HTTPStatus

from app.core.exceptions.base import AppException
from app.core.exceptions.common import (
    BadGatewayException,
    BadRequestException,
    InternalServerException,
    ServiceUnavailableException,
)


class PlaceSearchKeywordMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_SEARCH_KEYWORD_MISSING",
            message="검색어를 입력해주세요.",
        )


class PlaceSearchKeywordTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_SEARCH_KEYWORD_TOO_LONG",
            message="검색어는 50자 이하로 입력해주세요.",
        )


class UnsupportedPlaceSearchProviderException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_PLACE_SEARCH_PROVIDER",
            message="지원하지 않는 장소 검색 제공자입니다.",
        )


class PlaceSearchPageRequestInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PLACE_SEARCH_PAGE_REQUEST",
            message="페이지 요청 값이 올바르지 않습니다.",
        )


class PlaceSearchCoordinateInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PLACE_SEARCH_COORDINATE",
            message="올바르지 않은 위치 정보입니다.",
        )


class PlaceSearchRateLimitExceededException(AppException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_SEARCH_RATE_LIMIT_EXCEEDED",
            message="장소 검색 요청이 많습니다. 잠시 후 다시 시도해주세요.",
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
        )


class PlaceSearchFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_SEARCH_FAILED",
            message="장소 검색 중 오류가 발생했습니다.",
        )


class ExternalPlaceSearchApiFailedException(BadGatewayException):
    def __init__(self) -> None:
        super().__init__(
            code="EXTERNAL_PLACE_SEARCH_API_FAILED",
            message="장소 검색 정보를 불러오지 못했습니다.",
        )


class ExternalPlaceSearchServiceUnavailableException(ServiceUnavailableException):
    def __init__(self) -> None:
        super().__init__(
            code="EXTERNAL_PLACE_SEARCH_SERVICE_UNAVAILABLE",
            message="장소 검색 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )
