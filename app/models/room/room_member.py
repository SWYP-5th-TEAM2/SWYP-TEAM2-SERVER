import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin
from app.models.room.enums import RoomMemberRole


class RoomMember(Base, TimestampMixin):
    __tablename__ = "room_members"

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="방 가입자 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 ID",
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="방 ID",
    )

    role: Mapped[RoomMemberRole] = mapped_column(
        Enum(RoomMemberRole, name="room_member_role"),
        nullable=False,
        default=RoomMemberRole.MEMBER,
        server_default=RoomMemberRole.MEMBER.value,
        comment="방 멤버 역할",
    )
