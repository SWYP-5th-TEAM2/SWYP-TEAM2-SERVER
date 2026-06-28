import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin


class Vote(Base, TimestampMixin):
    __tablename__ = "votes"

    __table_args__ = (
        UniqueConstraint("user_id", "plan_id", name="uq_votes_user_plan"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="일정 투표 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 ID",
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="계획 ID",
    )

    is_attending: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="참석 여부",
    )
