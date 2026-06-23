import uuid
from datetime import date

from sqlalchemy import Enum, String, Date, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin
from app.models.user.enums import Provider, Gender, UserRole, UserAccountStatus


class User(Base, TimestampMixin):
    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uq_users_provider_provider_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="사용자 ID",
    )

    provider: Mapped[Provider] = mapped_column(
        Enum(Provider, name="oauth_provider"),
        nullable=False,
        comment="소셜 로그인 제공자",
    )

    provider_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Provider에서 제공된 식별자",
    )

    nickname: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="사용자 이름",
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Provider에서 제공된 이메일",
    )

    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="gender"),
        nullable=True,
        comment="성별",
    )

    birthday: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="생년월일",
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        comment="사용자 권한",
    )

    status: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus, name="user_account_status"),
        nullable=False,
        default=UserAccountStatus.ACTIVE,
        server_default=UserAccountStatus.ACTIVE.value,
        comment="사용자 계정 상태",
    )

    candidate_place_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="딸깍 생성 알림 활성화 여부",
    )

    vote_deadline_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="투표 마감 알림 활성화 여부",
    )

    schedule_confirmed_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="일정 확정 알림 활성화 여부",
    )

    quiet_recommendation_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="일정 생성 권유 알림 활성화 여부",
    )