from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import (
    Image,
    Notification,
    Place,
    Plan,
    RecurringScheduleGroup,
    RoomMember,
    User,
    UserFcmToken,
    UserWithdrawalReason,
    Vote,
)
from app.models.user.enums import UserAccountStatus, WithdrawalReason


def create_user_withdrawal_reasons(
    db: Session,
    *,
    user_id: UUID,
    reasons: list[WithdrawalReason],
) -> None:
    db.add_all(
        [
            UserWithdrawalReason(
                user_id=user_id,
                reason=reason,
            )
            for reason in reasons
        ],
    )


def mask_user_fcm_tokens(
    db: Session,
    *,
    user_id: UUID,
    withdrawn_at: datetime,
) -> None:
    stmt = select(UserFcmToken).where(UserFcmToken.user_id == user_id)
    fcm_tokens = db.execute(stmt).scalars().all()

    for fcm_token in fcm_tokens:
        # fcm_token 마스킹 처리
        fcm_token.fcm_token = f"withdrawn:{fcm_token.id}"
        fcm_token.is_active = False
        if fcm_token.deleted_at is None:
            fcm_token.deleted_at = withdrawn_at


def soft_delete_user_related_records(
    db: Session,
    *,
    user_id: UUID,
    withdrawn_at: datetime,
) -> None:
    soft_delete_models = (
        RoomMember,
        Image,
        Notification,
        Vote,
    )

    for model in soft_delete_models:
        stmt = (
            update(model)
            .where(
                model.user_id == user_id,
                model.deleted_at.is_(None),
            )
            .values(deleted_at=withdrawn_at)
        )
        db.execute(stmt)

    recurring_schedule_stmt = (
        update(RecurringScheduleGroup)
        .where(
            RecurringScheduleGroup.user_id == user_id,
            RecurringScheduleGroup.deleted_at.is_(None),
        )
        .values(
            is_enabled=False,
            deleted_at=withdrawn_at,
        )
    )
    db.execute(recurring_schedule_stmt)


def disconnect_user_from_retained_records(
    db: Session,
    *,
    user_id: UUID,
) -> None:
    plan_stmt = (
        update(Plan)
        .where(Plan.creator_id == user_id)
        .values(creator_id=None)
    )
    db.execute(plan_stmt)

    place_stmt = (
        update(Place)
        .where(Place.user_id == user_id)
        .values(user_id=None)
    )
    db.execute(place_stmt)


def mark_user_as_withdrawn(
    user: User,
    *,
    withdrawn_at: datetime,
) -> None:
    user.status = UserAccountStatus.WITHDRAWN
    user.profile_image_id = None
    user.deleted_at = withdrawn_at
