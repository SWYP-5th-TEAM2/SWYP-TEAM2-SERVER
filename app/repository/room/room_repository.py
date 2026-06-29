from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Room, RoomMember, RoomMemberRole


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


def find_room_by_invite_code(
    db: Session,
    *,
    invite_code: str,
) -> Room | None:
    stmt = select(Room).where(
        Room.invite_code == invite_code,
        Room.deleted_at.is_(None),
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
