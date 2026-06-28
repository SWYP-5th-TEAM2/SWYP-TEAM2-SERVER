import uuid

from sqlalchemy import UniqueConstraint, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.user.enums import WithdrawalReason


class UserWithdrawalReason(Base):
    __tablename__ = "user_withdrawal_reasons"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "reason",
            name="uq_user_withdrawal_reasons_user_id_reason",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="탈퇴 사유 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="사용자 ID",
    )

    reason: Mapped[WithdrawalReason] = mapped_column(
        Enum(WithdrawalReason, name="withdrawal_reason"),
        nullable=False,
        comment="탈퇴 사유",
    )
