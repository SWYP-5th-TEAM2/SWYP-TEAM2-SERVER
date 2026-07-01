from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Image,
    Notification,
    NotificationTargetType,
    NotificationType,
    Place,
    Plan,
    PlanStatus,
    Room,
    RoomMember,
    RoomMemberRole,
    User,
    UserFcmToken,
    Vote,
)

ACTIVE_PLAN_STATUSES = {PlanStatus.VOTING, PlanStatus.CONFIRMED}


def count_drawable_places(db: Session, *, room_id: UUID) -> int:
    stmt = select(func.count(Place.id)).where(
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
    )
    return int(db.execute(stmt).scalar_one())


def find_random_drawable_place(
    db: Session,
    *,
    room_id: UUID,
    exclude_place_id: UUID | None = None,
) -> tuple[Place, str | None] | None:
    conditions = [
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
    ]
    if exclude_place_id is not None:
        conditions.append(Place.id != exclude_place_id)

    stmt = (
        select(Place, User.nickname)
        .outerjoin(User, User.id == Place.user_id)
        .where(*conditions)
        .order_by(func.random())
        .limit(1)
    )
    row = db.execute(stmt).one_or_none()
    if row is None:
        return None
    place, nickname = row
    return place, nickname


def find_place_in_room(
    db: Session,
    *,
    place_id: UUID,
    room_id: UUID,
) -> Place | None:
    stmt = select(Place).where(
        Place.id == place_id,
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()


def find_active_plan_for_place(
    db: Session,
    *,
    room_id: UUID,
    place_id: UUID,
) -> Plan | None:
    stmt = (
        select(Plan)
        .where(
            Plan.room_id == room_id,
            Plan.place_id == place_id,
            Plan.deleted_at.is_(None),
            Plan.status.in_(ACTIVE_PLAN_STATUSES),
        )
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def count_target_members(
    db: Session,
    *,
    room_id: UUID,
    excluded_user_id: UUID,
) -> int:
    stmt = select(func.count(RoomMember.id)).where(
        RoomMember.room_id == room_id,
        RoomMember.user_id != excluded_user_id,
        RoomMember.deleted_at.is_(None),
    )
    return int(db.execute(stmt).scalar_one())


def find_target_member_previews(
    db: Session,
    *,
    room_id: UUID,
    excluded_user_id: UUID,
    limit: int | None = None,
) -> list[tuple[UUID, str | None, str | None]]:
    stmt = (
        select(User.id, User.nickname, Image.image_url)
        .join(RoomMember, RoomMember.user_id == User.id)
        .outerjoin(
            Image,
            and_(
                Image.id == User.profile_image_id,
                Image.deleted_at.is_(None),
            ),
        )
        .where(
            RoomMember.room_id == room_id,
            RoomMember.user_id != excluded_user_id,
            RoomMember.deleted_at.is_(None),
            User.deleted_at.is_(None),
        )
        .order_by(RoomMember.created_at.asc(), RoomMember.id.asc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).all())


def create_plan_row(
    db: Session,
    *,
    room_id: UUID,
    place_id: UUID,
    creator_id: UUID,
    name: str | None,
    start_time: datetime,
    voting_ends_at: datetime,
) -> Plan:
    plan = Plan(
        room_id=room_id,
        place_id=place_id,
        creator_id=creator_id,
        status=PlanStatus.VOTING,
        name=name,
        start_time=start_time,
        voting_ends_at=voting_ends_at,
    )
    db.add(plan)
    db.flush()
    return plan


def create_notifications(
    db: Session,
    *,
    user_ids: list[UUID],
    notification_type: NotificationType,
    title: str,
    content: str,
    target_type: NotificationTargetType | None,
    target_id: UUID | None,
) -> list[Notification]:
    notifications = [
        Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            target_type=target_type,
            target_id=target_id,
        )
        for user_id in user_ids
    ]
    if notifications:
        db.add_all(notifications)
        db.flush()
    return notifications


def count_active_fcm_tokens(
    db: Session,
    *,
    user_ids: list[UUID],
) -> int:
    if not user_ids:
        return 0
    stmt = select(func.count(UserFcmToken.id)).where(
        UserFcmToken.user_id.in_(user_ids),
        UserFcmToken.is_active.is_(True),
        UserFcmToken.deleted_at.is_(None),
    )
    return int(db.execute(stmt).scalar_one())


def find_plan_by_id_including_deleted(db: Session, *, plan_id: UUID) -> Plan | None:
    stmt = select(Plan).where(Plan.id == plan_id)
    return db.execute(stmt).scalar_one_or_none()


def find_plan_place_room_row(
    db: Session,
    *,
    plan_id: UUID,
) -> tuple[Plan, Place | None, Room | None, str | None, str | None] | None:
    creator = User
    stmt = (
        select(Plan, Place, Room, creator.nickname, Image.image_url)
        .outerjoin(Place, Place.id == Plan.place_id)
        .outerjoin(Room, Room.id == Plan.room_id)
        .outerjoin(creator, creator.id == Plan.creator_id)
        .outerjoin(
            Image,
            and_(
                Image.id == creator.profile_image_id,
                Image.deleted_at.is_(None),
            ),
        )
        .where(Plan.id == plan_id)
    )
    return db.execute(stmt).one_or_none()


def find_votes_by_plan_id(db: Session, *, plan_id: UUID) -> list[Vote]:
    stmt = select(Vote).where(
        Vote.plan_id == plan_id,
        Vote.deleted_at.is_(None),
    )
    return list(db.execute(stmt).scalars().all())


def find_vote_by_plan_and_user(
    db: Session,
    *,
    plan_id: UUID,
    user_id: UUID,
) -> Vote | None:
    stmt = select(Vote).where(
        Vote.plan_id == plan_id,
        Vote.user_id == user_id,
        Vote.deleted_at.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()


def find_room_member_response_rows(
    db: Session,
    *,
    room_id: UUID,
    excluded_user_id: UUID | None,
) -> list[tuple[UUID, str | None, str | None, RoomMemberRole]]:
    conditions = [
        RoomMember.room_id == room_id,
        RoomMember.deleted_at.is_(None),
        User.deleted_at.is_(None),
    ]
    if excluded_user_id is not None:
        conditions.append(RoomMember.user_id != excluded_user_id)

    stmt = (
        select(User.id, User.nickname, Image.image_url, RoomMember.role)
        .join(User, User.id == RoomMember.user_id)
        .outerjoin(
            Image,
            and_(
                Image.id == User.profile_image_id,
                Image.deleted_at.is_(None),
            ),
        )
        .where(*conditions)
        .order_by(
            case((RoomMember.role == RoomMemberRole.HOST, 0), else_=1),
            RoomMember.created_at.asc(),
            RoomMember.id.asc(),
        )
    )
    return list(db.execute(stmt).all())


def find_members_by_ids(
    db: Session,
    *,
    user_ids: list[UUID],
) -> list[tuple[UUID, str | None, str | None]]:
    if not user_ids:
        return []
    stmt = (
        select(User.id, User.nickname, Image.image_url)
        .outerjoin(
            Image,
            and_(
                Image.id == User.profile_image_id,
                Image.deleted_at.is_(None),
            ),
        )
        .where(User.id.in_(user_ids), User.deleted_at.is_(None))
    )
    rows = list(db.execute(stmt).all())
    order = {user_id: index for index, user_id in enumerate(user_ids)}
    return sorted(rows, key=lambda row: order.get(row[0], len(order)))


def upsert_vote(
    db: Session,
    *,
    plan_id: UUID,
    user_id: UUID,
    is_attending: bool,
) -> Vote:
    vote = find_vote_by_plan_and_user(db=db, plan_id=plan_id, user_id=user_id)
    if vote is None:
        vote = Vote(plan_id=plan_id, user_id=user_id, is_attending=is_attending)
        db.add(vote)
    else:
        vote.is_attending = is_attending
    db.flush()
    return vote


def count_plans_by_status(
    db: Session,
    *,
    room_id: UUID,
    status: PlanStatus | None = None,
) -> int:
    conditions = [
        Plan.room_id == room_id,
        Plan.deleted_at.is_(None),
    ]
    if status is not None:
        conditions.append(Plan.status == status)
    stmt = select(func.count(Plan.id)).where(*conditions)
    return int(db.execute(stmt).scalar_one())


def find_plan_list_rows(
    db: Session,
    *,
    room_id: UUID,
    statuses: list[PlanStatus] | None,
    offset: int,
    limit: int,
) -> list[tuple[Plan, Place | None]]:
    conditions = [
        Plan.room_id == room_id,
        Plan.deleted_at.is_(None),
    ]
    if statuses:
        conditions.append(Plan.status.in_(statuses))
    stmt = (
        select(Plan, Place)
        .outerjoin(Place, Place.id == Plan.place_id)
        .where(*conditions)
        .order_by(Plan.created_at.desc(), Plan.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(stmt).all())
