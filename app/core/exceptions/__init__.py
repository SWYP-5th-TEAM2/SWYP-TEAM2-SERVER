from app.core.exceptions.base import AppException
from app.core.exceptions.common import *
from app.core.exceptions.auth import *
from app.core.exceptions.external import *
from app.core.exceptions.user import *
from app.core.exceptions.recurring_schedule import *
from app.core.exceptions.notification_settings import *
from app.core.exceptions.user_withdrawal import *
from app.core.exceptions.room import *

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

    # Notification Settings Exceptions
    "NotificationSettingsRequestBodyMissingException",
    "UnsupportedNotificationSettingException",
    "NotificationSettingsUpdateFieldsMissingException",
    "NotificationSettingValueInvalidException",
    "NotificationSettingsFailedException",

    # User Withdrawal Exceptions
    "UserWithdrawalRequestBodyMissingException",
    "WithdrawalReasonMissingException",
    "UserAlreadyWithdrawnException",
    "UserWithdrawalFailedException",

    # Room Exceptions
    "RoomRequestBodyMissingException",
    "RoomNameMissingException",
    "RoomNameTooLongException",
    "RoomNameInvalidException",
    "RoomColorMissingException",
    "RoomColorInvalidException",
    "RoomIdInvalidException",
    "InviteCodeMissingException",
    "InviteCodeInvalidException",
    "WithdrawnRoomUserException",
    "BlockedRoomUserException",
    "RoomAccessDeniedException",
    "RoomNotFoundException",
    "InviteCodeRoomNotFoundException",
    "RoomAlreadyJoinedException",
    "RoomCreateFailedException",
    "InviteCodeLookupFailedException",
    "RoomJoinFailedException",
    "RoomUnavailableException",
    "RoomAlreadyLeftException",
    "RoomInfoLookupFailedException",
    "RoomLeaveFailedException",
    "RoomMemberUserIdInvalidException",
    "RoomHostRequiredException",
    "RoomMemberNotFoundException",
    "SelfKickNotAllowedException",
    "HostKickNotAllowedException",
    "RoomMemberAlreadyKickedException",
    "RoomMemberKickFailedException",
    "MyRoomsLookupFailedException",

    # External Exceptions
    "RedisUnavailableException",
]
