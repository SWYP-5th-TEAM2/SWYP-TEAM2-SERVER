from app.core.exceptions.common import (
    BadRequestException,
    InternalServerException,
    NotFoundException,
)


class FcmTokenMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="FCM_TOKEN_MISSING",
            message="FCM 토큰 입력은 필수입니다.",
        )


class FcmTokenBlankException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="FCM_TOKEN_BLANK",
            message="FCM 토큰은 비어있을 수 없습니다.",
        )


class DeviceTypeMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="DEVICE_TYPE_MISSING",
            message="기기 타입 입력은 필수입니다.",
        )


class UnsupportedDeviceTypeException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_DEVICE_TYPE",
            message="지원하지 않는 기기 유형입니다.",
        )


class UserNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
        )


class RequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="REQUEST_BODY_MISSING",
            message="요청 본문이 없습니다.",
        )


class ProfileUpdateFieldsMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PROFILE_UPDATE_FIELDS_MISSING",
            message="수정할 프로필 정보를 입력해주세요.",
        )


class InvalidNicknameFormatException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_NICKNAME_FORMAT",
            message="닉네임 형식이 올바르지 않습니다.",
        )


class NicknameTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="NICKNAME_TOO_LONG",
            message="닉네임은 최대 12자까지 입력할 수 있습니다.",
        )


class NicknameContainsInvalidCharacterException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="NICKNAME_CONTAINS_INVALID_CHARACTER",
            message="닉네임에 사용할 수 없는 문자가 포함되어 있습니다.",
        )


class InvalidProfileImageUrlException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_PROFILE_IMAGE_URL",
            message="프로필 이미지 URL 형식이 올바르지 않습니다.",
        )


class ProfileImageUrlNotAllowedException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="PROFILE_IMAGE_URL_NOT_ALLOWED",
            message="허용되지 않은 프로필 이미지 URL입니다.",
        )


class ProfileUpdateFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="PROFILE_UPDATE_FAILED",
            message="닉네임 수정 중 오류가 발생했습니다.",
        )


class TermsAgreementRequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="TERMS_AGREEMENT_REQUEST_BODY_MISSING",
            message="약관 동의 정보가 필요합니다.",
        )


class TermsAgreementFieldsMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="TERMS_AGREEMENT_FIELDS_MISSING",
            message="약관 동의 정보가 누락되었습니다.",
        )


class RequiredTermsNotAgreedException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="REQUIRED_TERMS_NOT_AGREED",
            message="필수 약관에 동의해야 합니다.",
        )


class TermsAgreementFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="TERMS_AGREEMENT_FAILED",
            message="서버 내부 오류가 발생했습니다.",
        )
