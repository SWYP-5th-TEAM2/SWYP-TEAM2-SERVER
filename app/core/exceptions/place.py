from http import HTTPStatus

from app.core.exceptions.base import AppException
from app.core.exceptions.common import (
    BadGatewayException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    ServiceUnavailableException,
)


class PlaceRequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_REQUEST_BODY_MISSING",
            message="요청 본문이 필요합니다.",
        )


class PlaceRoomIdMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_ROOM_ID_MISSING",
            message="방 ID를 입력해주세요.",
        )


class PlaceRoomIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PLACE_ROOM_ID",
            message="올바르지 않은 방 ID입니다.",
        )


class PlaceIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PLACE_ID",
            message="올바르지 않은 장소 후보 ID입니다.",
        )


class PlaceTitleMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_TITLE_MISSING",
            message="후보명을 입력해주세요.",
        )


class PlaceTitleTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_TITLE_TOO_LONG",
            message="후보명은 30자 이하로 입력해주세요.",
        )


class PlaceNameTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_NAME_TOO_LONG",
            message="장소명은 30자 이하로 입력해주세요.",
        )


class PlaceAddressTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_ADDRESS_TOO_LONG",
            message="장소 주소는 255자 이하로 입력해주세요.",
        )


class PlaceCoordinateInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PLACE_COORDINATE",
            message="올바르지 않은 위치 정보입니다.",
        )


class PlaceLinkUrlInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PLACE_LINK_URL",
            message="올바르지 않은 링크 형식입니다.",
        )


class UnsupportedPlaceLinkUrlException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_PLACE_LINK_URL",
            message="지원하지 않는 링크 형식입니다.",
        )


class PlaceImageUrlInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PLACE_IMAGE_URL",
            message="올바르지 않은 이미지 URL입니다.",
        )


class PlaceUpdateFieldsMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_UPDATE_FIELDS_MISSING",
            message="수정할 장소 후보 정보를 입력해주세요.",
        )


class PlacePageValueInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_PAGE_VALUE_INVALID",
            message="페이지 요청 값이 올바르지 않습니다.",
        )


class PlaceKeywordTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_KEYWORD_TOO_LONG",
            message="검색어는 30자 이하로 입력해주세요.",
        )


class PlaceRoomAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_ROOM_ACCESS_DENIED",
            message="해당 방에 접근할 권한이 없습니다.",
        )


class PlaceModifyAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_MODIFY_ACCESS_DENIED",
            message="장소 후보를 수정할 권한이 없습니다.",
        )


class PlaceDeleteAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_DELETE_ACCESS_DENIED",
            message="장소 후보를 삭제할 권한이 없습니다.",
        )


class PlaceRoomNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_ROOM_NOT_FOUND",
            message="존재하지 않는 방입니다.",
        )


class PlaceNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_NOT_FOUND",
            message="존재하지 않는 장소 후보입니다.",
        )


class PlaceDeletedException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_DELETED",
            message="삭제된 장소 후보입니다.",
        )


class PlaceAlreadyExistsException(ConflictException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_ALREADY_EXISTS",
            message="이미 후보함에 등록된 장소입니다.",
        )


class PlaceUsedInActivePlanException(ConflictException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_USED_IN_ACTIVE_PLAN",
            message="진행 중인 약속에 사용 중인 장소 후보입니다.",
        )


class PlaceListLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_LIST_LOOKUP_FAILED",
            message="후보함 조회 중 오류가 발생했습니다.",
        )


class PlaceDetailLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_DETAIL_LOOKUP_FAILED",
            message="장소 상세 정보 조회 중 오류가 발생했습니다.",
        )


class PlaceCreateFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_CREATE_FAILED",
            message="장소 후보 생성 중 오류가 발생했습니다.",
        )


class PlaceUpdateFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_UPDATE_FAILED",
            message="장소 후보 수정 중 오류가 발생했습니다.",
        )


class PlaceDeleteFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="PLACE_DELETE_FAILED",
            message="장소 후보 삭제 중 오류가 발생했습니다.",
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
