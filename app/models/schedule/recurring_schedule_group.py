import uuid
from datetime import time

from sqlalchemy import Boolean, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin


class RecurringScheduleGroup(Base, TimestampMixin):
    __tablename__ = "recurring_schedule_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="반복 일정 그룹 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 ID",
    )

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="반복 일정 사유",
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="활성화 여부",
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="시작 시간",
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="종료 시간",
    )
