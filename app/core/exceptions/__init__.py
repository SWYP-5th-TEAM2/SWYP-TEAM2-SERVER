from app.core.exceptions.base import AppException
from app.core.exceptions.common import *
from app.core.exceptions.auth import *

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
    "TokenExpiredException",
    "InvalidTokenException",
    "InvalidTokenTypeException",
    "BlockedUserException",
    "EmailAlreadyExistsException",
    "TokenIssueFailedException",
    "SocialUserInfoFetchFailedException",
    "ExternalAuthServiceUnavailableException"
]
