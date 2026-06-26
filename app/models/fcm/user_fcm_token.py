import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.fcm.enums import DeviceType
from app.models.mixins import TimestampMixin


class UserFcmToken(Base, TimestampMixin):
    __tablename__ = "user_fcm_tokens"

    __table_args__ = (
        UniqueConstraint("fcm_token", name="uq_user_fcm_tokens_fcm_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="FCM 토큰 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 ID",
    )

    fcm_token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="FCM 토큰",
    )

    device_type: Mapped[DeviceType] = mapped_column(
        Enum(DeviceType, name="device_type"),
        nullable=False,
        comment="사용 기기",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="푸시 전송 가능 여부",
    )
