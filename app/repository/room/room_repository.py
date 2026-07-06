from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Image,
    Place,
    Plan,
    PlanStatus,
    Room,
    RoomMember,
    RoomMemberRole,
    User,
    Vote,
)


def create_room_with_host(
    db: Session,
    *,
    user_id: UUID,
    room_name: str,
    room_color: str,
    invite_code: str,
) -> Room:
    room = Room(
        name=room_name,
        color=room_color,
        invite_code=invite_code,
    )
    db.add(room)
    db.flush()

    host = RoomMember(
        user_id=user_id,
        room_id=room.id,
        role=RoomMemberRole.HOST,
    )
    db.add(host)
    db.flush()

    return room


def find_room_by_id(
    db: Session,
    *,
    room_id: UUID,
) -> Room | None:
    stmt = select(Room).where(
        Room.id == room_id,
        Room.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_room_by_id_including_deleted(
    db: Session,
    *,
    room_id: UUID,
) -> Room | None:
    stmt = select(Room).where(Room.id == room_id)
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_active_room_by_id_for_update(
    db: Session,
    *,
    room_id: UUID,
) -> Room | None:
    stmt = (
        select(Room)
        .where(
            Room.id == room_id,
            Room.deleted_at.is_(None),
        )
        .with_for_update()
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_active_room_by_invite_code_for_update(
    db: Session,
    *,
    invite_code: str,
) -> Room | None:
    stmt = (
        select(Room)
        .where(
            Room.invite_code == invite_code,
            Room.deleted_at.is_(None),
        )
        .with_for_update()
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_active_room_member(
    db: Session,
    *,
    room_id: UUID,
    user_id: UUID,
) -> RoomMember | None:
    stmt = select(RoomMember).where(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
        RoomMember.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_room_member(
    db: Session,
    *,
    room_id: UUID,
    user_id: UUID,
) -> RoomMember | None:
    stmt = select(RoomMember).where(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_earliest_active_member(
    db: Session,
    *,
    room_id: UUID,
    excluded_user_id: UUID,
) -> RoomMember | None:
    stmt = (
        select(RoomMember)
        .where(
            RoomMember.room_id == room_id,
            RoomMember.user_id != excluded_user_id,
            RoomMember.role == RoomMemberRole.MEMBER,
            RoomMember.deleted_at.is_(None),
        )
        .order_by(
            RoomMember.created_at.asc(),
            RoomMember.id.asc(),
        )
        .limit(1)
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def find_room_member_details(
    db: Session,
    *,
    room_id: UUID,
) -> list[tuple[UUID, str | None, str | None, RoomMemberRole]]:
    stmt = (
        select(
            User.id,
            Image.image_url,
            User.nickname,
            RoomMember.role,
        )
        .join(User, User.id == RoomMember.user_id)
        .outerjoin(
            Image,
            and_(
                Image.id == User.profile_image_id,
                Image.user_id == User.id,
                Image.deleted_at.is_(None),
            ),
        )
        .where(
            RoomMember.room_id == room_id,
            RoomMember.deleted_at.is_(None),
        )
        .order_by(
            case(
                (RoomMember.role == RoomMemberRole.HOST, 0),
                else_=1,
            ),
            RoomMember.created_at.asc(),
            RoomMember.id.asc(),
        )
    )
    result = db.execute(stmt)
    return [
        (member_id, profile_image, nickname, role)
        for member_id, profile_image, nickname, role in result.all()
    ]


def count_active_places_by_room_id(
    db: Session,
    *,
    room_id: UUID,
) -> int:
    stmt = select(func.count(Place.id)).where(
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return int(result.scalar_one())


def find_my_active_rooms(
    db: Session,
    *,
    user_id: UUID,
    keyword: str | None,
) -> list[Room]:
    conditions = [
        RoomMember.user_id == user_id,
        RoomMember.deleted_at.is_(None),
        Room.deleted_at.is_(None),
    ]
    if keyword:
        conditions.append(Room.name.ilike(f"%{keyword}%"))

    stmt = (
        select(Room)
        .join(RoomMember, RoomMember.room_id == Room.id)
        .where(*conditions)
        .order_by(RoomMember.created_at.desc(), Room.created_at.desc())
    )
    result = db.execute(stmt)
    return list(result.scalars().all())


def count_active_room_members(
    db: Session,
    *,
    room_id: UUID,
) -> int:
    stmt = select(func.count(RoomMember.id)).where(
        RoomMember.room_id == room_id,
        RoomMember.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return int(result.scalar_one())


def find_random_room_member_previews(
    db: Session,
    *,
    room_id: UUID,
    limit: int,
) -> list[tuple[str, str | None]]:
    stmt = (
        select(
            User.nickname,
            Image.image_url,
        )
        .join(RoomMember, RoomMember.user_id == User.id)
        .outerjoin(
            Image,
            and_(
                Image.id == User.profile_image_id,
                Image.user_id == User.id,
                Image.deleted_at.is_(None),
            ),
        )
        .where(
            RoomMember.room_id == room_id,
            RoomMember.deleted_at.is_(None),
        )
        .order_by(func.random())
        .limit(limit)
    )
    result = db.execute(stmt)
    return [
        (nickname or "", profile_image)
        for nickname, profile_image in result.all()
    ]


def find_representative_plan_by_room_id(
    db: Session,
    *,
    room_id: UUID,
    current_time: datetime,
) -> Plan | None:
    stmt = (
        select(Plan)
        .where(
            Plan.room_id == room_id,
            Plan.deleted_at.is_(None),
            or_(
                and_(
                    Plan.status == PlanStatus.VOTING,
                    Plan.voting_ends_at > current_time,
                ),
                Plan.status == PlanStatus.CONFIRMED,
                Plan.status == PlanStatus.COMPLETED,
            ),
        )
        .order_by(
            case(
                (Plan.status == PlanStatus.VOTING, 0),
                (Plan.status == PlanStatus.CONFIRMED, 1),
                (Plan.status == PlanStatus.COMPLETED, 2),
                else_=3,
            ),
            case(
                (Plan.status == PlanStatus.VOTING, Plan.voting_ends_at),
                (Plan.status == PlanStatus.CONFIRMED, Plan.start_time),
                else_=None,
            ).asc(),
            desc(Plan.updated_at),
        )
        .limit(1)
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def count_votes_by_plan_id(
    db: Session,
    *,
    plan_id: UUID,
) -> int:
    stmt = select(func.count(Vote.id)).where(
        Vote.plan_id == plan_id,
        Vote.deleted_at.is_(None),
    )
    result = db.execute(stmt)
    return int(result.scalar_one())


def create_room_member(
    db: Session,
    *,
    room_id: UUID,
    user_id: UUID,
) -> RoomMember:
    room_member = RoomMember(
        room_id=room_id,
        user_id=user_id,
        role=RoomMemberRole.MEMBER,
    )
    db.add(room_member)
    db.flush()
    return room_member
