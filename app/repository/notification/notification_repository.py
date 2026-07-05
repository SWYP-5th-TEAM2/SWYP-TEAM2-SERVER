from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.models import Image, Notification, NotificationTargetType, Place, Plan, Room, User, Vote


def _notification_room_filter(room_id: UUID):
    """Return a SQL condition that resolves a notification to a room.

    notifications 테이블에는 room_id 컬럼이 없고, target_type/target_id만 있다.
    따라서 알림 타입별 이동 대상에서 room_id를 역추적해 roomId 필터를 적용한다.
    - PLAN 알림: target_id -> plans.id -> plans.room_id
    - VOTE 알림: target_id -> votes.id -> votes.plan_id -> plans.room_id
    - ROOM 알림: target_id 자체가 room_id
    - PLACE 알림: target_id -> places.id -> places.room_id
    """
    plan_ids_in_room = select(Plan.id).where(
        Plan.room_id == room_id,
        Plan.deleted_at.is_(None),
    )
    vote_ids_in_room = (
        select(Vote.id)
        .join(Plan, Plan.id == Vote.plan_id)
        .where(
            Plan.room_id == room_id,
            Plan.deleted_at.is_(None),
            Vote.deleted_at.is_(None),
        )
    )
    place_ids_in_room = select(Place.id).where(
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
    )
    return or_(
        and_(
            Notification.target_type == NotificationTargetType.PLAN,
            Notification.target_id.in_(plan_ids_in_room),
        ),
        and_(
            Notification.target_type == NotificationTargetType.VOTE,
            Notification.target_id.in_(vote_ids_in_room),
        ),
        and_(
            Notification.target_type == NotificationTargetType.ROOM,
            Notification.target_id == room_id,
        ),
        and_(
            Notification.target_type == NotificationTargetType.PLACE,
            Notification.target_id.in_(place_ids_in_room),
        ),
    )


def _notification_list_conditions(*, user_id: UUID, room_id: UUID | None):
    conditions = [
        Notification.user_id == user_id,
        Notification.deleted_at.is_(None),
    ]
    if room_id is not None:
        conditions.append(_notification_room_filter(room_id))
    return conditions


def count_notifications_for_user(db: Session, *, user_id: UUID, room_id: UUID | None = None) -> int:
    stmt = select(func.count(Notification.id)).where(
        *_notification_list_conditions(user_id=user_id, room_id=room_id),
    )
    return int(db.execute(stmt).scalar_one())


def find_notifications_for_user(
    db: Session,
    *,
    user_id: UUID,
    offset: int,
    limit: int,
    room_id: UUID | None = None,
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(
            *_notification_list_conditions(user_id=user_id, room_id=room_id),
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
