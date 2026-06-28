from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.models import Image, RecurringScheduleGroup, Room, RoomMember


def find_user_image_by_id(
    db: Session,
    *,
    user_id: UUID,
    image_id: UUID,
) -> Image | None:
    stmt = select(Image).where(
        Image.id == image_id,
        Image.user_id == user_id,
        Image.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_user_image_by_url(
    db: Session,
    *,
    user_id: UUID,
    image_url: str,
) -> Image | None:
    stmt = (
        select(Image)
        .where(
            Image.user_id == user_id,
            Image.image_url == image_url,
            Image.deleted_at.is_(None),
        )
        .order_by(Image.created_at.desc())
        .limit(1)
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_room_summaries_by_user_id(
    db: Session,
    *,
    user_id: UUID,
) -> list[tuple[UUID, str, int]]:
    current_membership = aliased(RoomMember)
    room_members = aliased(RoomMember)

    stmt = (
        select(
            Room.id,
            Room.name,
            func.count(room_members.id),
        )
        .join(
            current_membership,
            current_membership.room_id == Room.id,
        )
        .outerjoin(
            room_members,
            and_(
                room_members.room_id == Room.id,
                room_members.deleted_at.is_(None),
            ),
        )
        .where(
            current_membership.user_id == user_id,
            current_membership.deleted_at.is_(None),
            Room.deleted_at.is_(None),
        )
        .group_by(Room.id, Room.name, Room.created_at)
        .order_by(Room.created_at.desc())
    )

    result = db.execute(stmt)
    return [
        (room_id, room_name, member_count)
        for room_id, room_name, member_count in result.all()
    ]


def count_recurring_schedule_groups_by_user_id(
    db: Session,
    *,
    user_id: UUID,
) -> int:
    stmt = select(func.count(RecurringScheduleGroup.id)).where(
        RecurringScheduleGroup.user_id == user_id,
        RecurringScheduleGroup.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return int(result.scalar_one())
