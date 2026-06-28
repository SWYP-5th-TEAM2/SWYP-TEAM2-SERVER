from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AppException,
    UserAlreadyWithdrawnException,
    UserNotFoundException,
    UserWithdrawalFailedException,
    UserWithdrawalRequestBodyMissingException,
    WithdrawalReasonMissingException,
)
from app.core.security.jwt import get_expires_at, get_jti
from app.core.security.token_store import (
    blacklist_access_token,
    delete_refresh_sessions_by_user_id,
)
from app.models.user.enums import UserAccountStatus, WithdrawalReason
from app.repository.user import (
    create_user_withdrawal_reasons,
    disconnect_user_from_retained_records,
    find_user_by_id,
    mark_user_as_withdrawn,
    mask_user_fcm_tokens,
    soft_delete_user_related_records,
)
from app.schemas.user import UserWithdrawalRequest
from app.services.auth.oauth.unlink import unlink_social_account


def _parse_withdrawal_reasons(
    reasons: list[str] | None,
) -> list[WithdrawalReason]:
    if not reasons:
        raise WithdrawalReasonMissingException()

    parsed_reasons: list[WithdrawalReason] = []
    for reason in reasons:
        try:
            parsed_reasons.append(
                WithdrawalReason(reason.strip().upper()),
            )
        except ValueError:
            parsed_reasons.append(WithdrawalReason.ETC)

    # 알 수 없는 코드가 ETC로 매핑되거나 같은 코드가 반복되어도 한 행만 저장한다.
    return list(dict.fromkeys(parsed_reasons))


async def withdraw_user(
    db: Session,
    redis: Redis,
    *,
    user_id: UUID,
    access_payload: dict[str, Any],
    request: UserWithdrawalRequest | None,
) -> None:
    if request is None:
        raise UserWithdrawalRequestBodyMissingException()

    withdrawal_reasons = _parse_withdrawal_reasons(request.withdraw_reason)
    access_jti = get_jti(access_payload)
    access_expires_at = get_expires_at(access_payload)
    withdrawn_at = datetime.now(timezone.utc)

    try:
        user = find_user_by_id(
            db=db,
            user_id=user_id,
        )
        if user is None:
            raise UserNotFoundException()

        if (
            user.status == UserAccountStatus.WITHDRAWN
            or user.deleted_at is not None
        ):
            raise UserAlreadyWithdrawnException()

        # 탈퇴 사유는 사용자별 enum 목록으로 보존한다.
        create_user_withdrawal_reasons(
            db=db,
            user_id=user_id,
            reasons=withdrawal_reasons,
        )

        # 소유 데이터(image, notification, vote, room_member, recurring_schedule_group)는 soft delete
        # 유지할 데이터(plan/place)는 사용자 연결만 해제
        mask_user_fcm_tokens(
            db=db,
            user_id=user_id,
            withdrawn_at=withdrawn_at,
        )
        soft_delete_user_related_records(
            db=db,
            user_id=user_id,
            withdrawn_at=withdrawn_at,
        )
        disconnect_user_from_retained_records(
            db=db,
            user_id=user_id,
        )
        mark_user_as_withdrawn(
            user,
            withdrawn_at=withdrawn_at,
        )

        # FK, nullable, unique 제약 위반을 외부 시스템 처리 전에 확인
        db.flush()

        # provider별 실제 연결 해제 로직
        await unlink_social_account(
            provider=user.provider,
            provider_id=user.provider_id,
        )

        # 로그아웃으로 처리하고 현재 access token도 즉시 폐기
        await delete_refresh_sessions_by_user_id(
            redis=redis,
            user_id=user_id,
        )
        await blacklist_access_token(
            redis=redis,
            jti=access_jti,
            expires_at=access_expires_at,
        )

        db.commit()
    except AppException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise UserWithdrawalFailedException() from exc
