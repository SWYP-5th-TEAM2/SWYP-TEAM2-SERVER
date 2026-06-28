from app.core.exceptions.common import (
    BadRequestException,
    ConflictException,
    InternalServerException,
)


class UserWithdrawalRequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_WITHDRAWAL_REQUEST_BODY_MISSING",
            message="요청 본문이 필요합니다.",
        )


class WithdrawalReasonMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="WITHDRAWAL_REASON_MISSING",
            message="탈퇴 사유를 입력해주세요.",
        )


class UserAlreadyWithdrawnException(ConflictException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_ALREADY_WITHDRAWN",
            message="이미 탈퇴한 회원입니다.",
        )


class UserWithdrawalFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_WITHDRAWAL_FAILED",
            message="회원탈퇴 처리 중 오류가 발생했습니다.",
        )
