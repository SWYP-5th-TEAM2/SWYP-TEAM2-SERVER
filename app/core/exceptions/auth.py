from app.core.exceptions import BadRequestException, UnauthorizedException, ForbiddenException, ConflictException, \
    InternalServerException, BadGatewayException, ServiceUnavailableException


# 400 BAD REQUEST
class UnsupportedProviderException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_PROVIDER",
            message="지원하지 않는 소셜 로그인 제공자입니다.",
        )

class AuthorizationCodeMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="AUTHORIZATION_CODE_MISSING",
            message="인가 코드가 필요합니다.",
        )

class InvalidAuthorizationCodeException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_AUTHORIZATION_CODE",
            message="유효하지 않은 인가 코드입니다.",
        )

class RequiredUserInfoMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="REQUIRED_USER_INFO_MISSING",
            message="필수 사용자 정보가 없습니다.",
        )


# 401 UNAUTHORIZED
class AuthorizationCodeExpiredException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="AUTHORIZATION_CODE_EXPIRED",
            message="만료 또는 사용된 인가 코드입니다.",
        )

class SocialLoginFailedException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="SOCIAL_LOGIN_FAILED",
            message="소셜 로그인 인증에 실패했습니다.",
        )

class TokenMissingException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="TOKEN_MISSING",
            message="인증 토큰이 필요합니다.",
        )

class AuthorizationHeaderMissingException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="AUTHORIZATION_HEADER_MISSING",
            message="Authorization 헤더가 필요합니다.",
        )

class AccessTokenMissingException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="ACCESS_TOKEN_MISSING",
            message="액세스 토큰이 필요합니다.",
        )

class TokenExpiredException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="TOKEN_EXPIRED",
            message="만료된 토큰입니다.",
        )

class InvalidTokenException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_TOKEN",
            message="유효하지 않은 토큰입니다.",
        )

class AccessTokenExpiredException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="ACCESS_TOKEN_EXPIRED",
            message="액세스 토큰이 만료되었습니다.",
        )

class InvalidAccessTokenException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_ACCESS_TOKEN",
            message="유효하지 않은 액세스 토큰입니다.",
        )

class InvalidTokenTypeException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_TOKEN_TYPE",
            message="토큰 타입이 올바르지 않습니다.",
        )

class RefreshTokenReusedException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="REFRESH_TOKEN_REUSED",
            message="이미 사용된 Refresh Token입니다.",
        )

class LoggedOutTokenException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__(
            code="LOGGED_OUT_TOKEN",
            message="이미 로그아웃된 토큰입니다.",
        )


# 403 FORBIDDEN
class BlockedUserException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            code="BLOCKED_USER",
            message="이용이 제한된 계정입니다.",
        )


# 409 CONFLICT
class EmailAlreadyExistsException(ConflictException):
    def __init__(self) -> None:
        super().__init__(
            code="EMAIL_ALREADY_EXISTS",
            message="이미 가입된 이메일입니다.",
        )


# 500 INTERNAL SERVER ERROR
class TokenIssueFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="TOKEN_ISSUE_FAILED",
            message="로그인 처리 중 오류가 발생했습니다.",
        )


class AppleOAuthConfigurationException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="APPLE_OAUTH_CONFIGURATION_ERROR",
            message="Apple 로그인 설정이 올바르지 않습니다.",
        )


# 502 BAD GATEWAY
class SocialUserInfoFetchFailedException(BadGatewayException):
    def __init__(self) -> None:
        super().__init__(
            code="SOCIAL_USER_INFO_FETCH_FAILED",
            message="소셜 계정 정보를 불러오지 못했습니다.",
        )


# 503 SERVICE UNAVAILABLE
class ExternalAuthServiceUnavailableException(ServiceUnavailableException):
    def __init__(self) -> None:
        super().__init__(
            code="EXTERNAL_AUTH_SERVICE_UNAVAILABLE",
            message="일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )
