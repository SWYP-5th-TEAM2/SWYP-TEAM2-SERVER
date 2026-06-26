import uuid
from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin
from app.models.notification.enums import NotificationTargetType, NotificationType


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="알림 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="알림 수신 사용자 ID",
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
        comment="알림 유형",
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="알림 제목",
    )

    content: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="알림 본문",
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="읽음 여부",
    )

    target_type: Mapped[NotificationTargetType | None] = mapped_column(
        Enum(NotificationTargetType, name="notification_target_type"),
        nullable=True,
        comment="알림 이동 대상 유형",
    )

    target_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="알림 이동 대상 ID",
    )
