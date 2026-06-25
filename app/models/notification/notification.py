import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin
from app.models.notification.enums import (
    NotificationTargetType,
    NotificationType,
    NotificationViewType,
)


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

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="알림 발생 사용자 ID",
    )

    room_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="알림 관련 방 ID",
    )

    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="알림 관련 계획 ID",
    )

    place_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("places.id", ondelete="SET NULL"),
        nullable=True,
        comment="알림 관련 장소 ID",
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
        comment="알림 이동 대상 ID",
    )

    view_type: Mapped[NotificationViewType | None] = mapped_column(
        Enum(NotificationViewType, name="notification_view_type"),
        nullable=True,
        comment="앱 이동 화면 유형",
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="알림 읽음 처리 일시",
    )
