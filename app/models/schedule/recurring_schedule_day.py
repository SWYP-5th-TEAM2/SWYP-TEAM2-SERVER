import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.schedule.enums import DayOfWeek


class RecurringScheduleDay(Base):
    __tablename__ = "recurring_schedule_day"

    __table_args__ = (
        UniqueConstraint(
            "recurring_schedule_group_id",
            "day_of_week",
            name="uq_recurring_schedule_day_group_day",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="반복 일정 요일 ID",
    )

    recurring_schedule_group_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("recurring_schedule_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="반복 일정 그룹 ID",
    )

    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Enum(DayOfWeek, name="day_of_week"),
        nullable=False,
        comment="요일",
    )
