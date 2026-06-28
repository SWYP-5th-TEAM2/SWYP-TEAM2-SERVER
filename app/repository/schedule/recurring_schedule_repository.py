from datetime import datetime, time
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import DayOfWeek, RecurringScheduleDay, RecurringScheduleGroup


def find_recurring_schedule_groups_by_user_id(
    db: Session,
    *,
    user_id: UUID,
) -> list[RecurringScheduleGroup]:
    stmt = (
        select(RecurringScheduleGroup)
        .where(
            RecurringScheduleGroup.user_id == user_id,
            RecurringScheduleGroup.deleted_at.is_(None),
        )
        .order_by(RecurringScheduleGroup.created_at.desc())
    )
    result = db.execute(stmt)
    return list(result.scalars().all())


def find_recurring_schedule_group_by_id(
    db: Session,
    *,
    user_id: UUID,
    recurring_schedule_id: UUID,
) -> RecurringScheduleGroup | None:
    stmt = select(RecurringScheduleGroup).where(
        RecurringScheduleGroup.id == recurring_schedule_id,
        RecurringScheduleGroup.user_id == user_id,
        RecurringScheduleGroup.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_recurring_schedule_days_by_group_ids(
    db: Session,
    *,
    recurring_schedule_group_ids: list[UUID],
) -> list[tuple[UUID, DayOfWeek]]:
    if not recurring_schedule_group_ids:
        return []

    stmt = select(
        RecurringScheduleDay.recurring_schedule_group_id,
        RecurringScheduleDay.day_of_week,
    ).where(
        RecurringScheduleDay.recurring_schedule_group_id.in_(
            recurring_schedule_group_ids,
        ),
    )
    result = db.execute(stmt)
    return [
        (group_id, day_of_week)
        for group_id, day_of_week in result.all()
    ]


def create_recurring_schedule(
    db: Session,
    *,
    user_id: UUID,
    title: str,
    days_of_week: list[DayOfWeek],
    start_time: time,
    end_time: time,
) -> RecurringScheduleGroup:
    recurring_schedule = RecurringScheduleGroup(
        user_id=user_id,
        title=title,
        is_enabled=True,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(recurring_schedule)
    db.flush()

    db.add_all(
        [
            RecurringScheduleDay(
                recurring_schedule_group_id=recurring_schedule.id,
                day_of_week=day_of_week,
            )
            for day_of_week in days_of_week
        ],
    )
    db.flush()
    return recurring_schedule


def replace_recurring_schedule_days(
    db: Session,
    *,
    recurring_schedule_group_id: UUID,
    days_of_week: list[DayOfWeek],
) -> None:
    stmt = delete(RecurringScheduleDay).where(
        RecurringScheduleDay.recurring_schedule_group_id
        == recurring_schedule_group_id,
    )
    db.execute(stmt)

    db.add_all(
        [
            RecurringScheduleDay(
                recurring_schedule_group_id=recurring_schedule_group_id,
                day_of_week=day_of_week,
            )
            for day_of_week in days_of_week
        ],
    )


def soft_delete_recurring_schedule(
    recurring_schedule: RecurringScheduleGroup,
    *,
    deleted_at: datetime,
) -> None:
    recurring_schedule.is_enabled = False
    recurring_schedule.deleted_at = deleted_at
