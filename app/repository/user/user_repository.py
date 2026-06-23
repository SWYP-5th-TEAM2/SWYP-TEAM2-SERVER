from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.models.user.enums import Provider, UserRole, UserAccountStatus


def find_user_by_provider(
    db: Session,
    *,
    provider: Provider,
    provider_id: str,
) -> User | None:
    stmt = select(User).where(
        User.provider == provider,
        User.provider_id == provider_id,
    )

    result = db.execute(stmt)
    return result.scalar_one_or_none()

def find_user_by_id(
        db: Session,
        user_id: UUID,
) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def create_user(
    db: Session,
    *,
    provider: Provider,
    provider_id: str,
    email: str | None,
    nickname: str | None,
) -> User:
    user = User(
        provider=provider,
        provider_id=provider_id,
        nickname=nickname,
        email=email,
        role=UserRole.USER,
        status=UserAccountStatus.ACTIVE,
    )

    db.add(user)
    db.flush()

    return user