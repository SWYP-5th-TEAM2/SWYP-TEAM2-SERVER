from app.core.exceptions.base import AppException
from app.core.exceptions.common import *
from app.core.exceptions.auth import *
from app.core.exceptions.external import *
from app.core.exceptions.user import *
from app.core.exceptions.recurring_schedule import *

__all__ = [
    "AppException",

    # Common Exceptions
    "BadRequestException",
    "ConflictException",
    "ForbiddenException",
    "NotFoundException",
    "UnauthorizedException",
    "InternalServerException",
    "BadGatewayException",
    "ServiceUnavailableException",

    # Auth Exceptions
    "UnsupportedProviderException",
    "AuthorizationCodeMissingException",
    "InvalidAuthorizationCodeException",
    "RequiredUserInfoMissingException",
    "AuthorizationCodeExpiredException",
    "SocialLoginFailedException",
    "TokenMissingException",
    "AuthorizationHeaderMissingException",
    "AccessTokenMissingException",
    "TokenExpiredException",
    "InvalidTokenException",
    "AccessTokenExpiredException",
    "InvalidAccessTokenException",
    "InvalidTokenTypeException",
    "RefreshTokenReusedException",
    "LoggedOutTokenException",
    "BlockedUserException",
    "EmailAlreadyExistsException",
    "TokenIssueFailedException",
    "SocialUserInfoFetchFailedException",
    "ExternalAuthServiceUnavailableException",

    # User Exceptions
    "FcmTokenMissingException",
    "FcmTokenBlankException",
    "DeviceTypeMissingException",
    "UnsupportedDeviceTypeException",
    "UserNotFoundException",
    "RequestBodyMissingException",
    "ProfileUpdateFieldsMissingException",
    "InvalidNicknameFormatException",
    "NicknameTooLongException",
    "NicknameContainsInvalidCharacterException",
    "InvalidProfileImageUrlException",
    "ProfileImageUrlNotAllowedException",
    "ProfileUpdateFailedException",

    # Recurring Schedule Exceptions
    "RecurringScheduleIdInvalidException",
    "RecurringScheduleRequestBodyMissingException",
    "RecurringScheduleUpdateFieldsMissingException",
    "RecurringScheduleActivationMissingException",
    "RecurringScheduleActivationInvalidException",
    "RecurringScheduleTitleMissingException",
    "RecurringScheduleTitleTooLongException",
    "RecurringScheduleDaysMissingException",
    "RecurringScheduleDayInvalidException",
    "RecurringScheduleDaysDuplicatedException",
    "RecurringScheduleStartTimeMissingException",
    "RecurringScheduleEndTimeMissingException",
    "RecurringScheduleTimeInvalidException",
    "RecurringScheduleTimeRangeInvalidException",
    "RecurringScheduleUserNotFoundException",
    "RecurringScheduleNotFoundException",
    "RecurringScheduleListFailedException",
    "RecurringScheduleCreateFailedException",
    "RecurringScheduleUpdateFailedException",
    "RecurringScheduleDeleteFailedException",

    # External Exceptions
    "RedisUnavailableException",
]
