from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session

from app.models import Image, Notification, Place, Plan, Room, User, Vote


def count_notifications_for_user(db: Session, *, user_id: UUID) -> int:
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.deleted_at.is_(None),
    )
    return int(db.execute(stmt).scalar_one())


def find_notifications_for_user(
    db: Session,
    *,
    user_id: UUID,
    offset: int,
    limit: int,
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
        )
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def find_notification_by_id_including_deleted(db: Session, *, notification_id: UUID) -> Notification | None:
    stmt = select(Notification).where(Notification.id == notification_id)
    return db.execute(stmt).scalar_one_or_none()


def mark_notification_read(db: Session, *, notification: Notification) -> Notification:
    notification.is_read = True
    db.flush()
    return notification


def mark_all_notifications_read(db: Session, *, user_id: UUID) -> int:
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    result = db.execute(stmt)
    db.flush()
    return int(result.rowcount or 0)


def find_user_preview_for_notification(
    db: Session,
    *,
    user_id: UUID | None,
) -> tuple[UUID, str | None, str | None] | None:
    if user_id is None:
        return None
    stmt = (
        select(User.id, User.nickname, Image.image_url)
        .outerjoin(
            Image,
            and_(
                Image.id == User.profile_image_id,
                Image.deleted_at.is_(None),
            ),
        )
        .where(User.id == user_id, User.deleted_at.is_(None))
    )
    return db.execute(stmt).one_or_none()


def find_plan_by_id_for_notification(db: Session, *, plan_id: UUID) -> Plan | None:
    stmt = select(Plan).where(Plan.id == plan_id)
    return db.execute(stmt).scalar_one_or_none()


def find_place_by_id_for_notification(db: Session, *, place_id: UUID) -> Place | None:
    stmt = select(Place).where(Place.id == place_id, Place.deleted_at.is_(None))
    return db.execute(stmt).scalar_one_or_none()


def find_room_by_id_for_notification(db: Session, *, room_id: UUID) -> Room | None:
    stmt = select(Room).where(Room.id == room_id, Room.deleted_at.is_(None))
    return db.execute(stmt).scalar_one_or_none()


def find_vote_by_id_for_notification(db: Session, *, vote_id: UUID) -> Vote | None:
    stmt = select(Vote).where(Vote.id == vote_id, Vote.deleted_at.is_(None))
    return db.execute(stmt).scalar_one_or_none()


def count_going_votes_for_plan(db: Session, *, plan_id: UUID) -> int:
    stmt = select(func.count(Vote.id)).where(
        Vote.plan_id == plan_id,
        Vote.is_attending.is_(True),
        Vote.deleted_at.is_(None),
    )
    return int(db.execute(stmt).scalar_one())
