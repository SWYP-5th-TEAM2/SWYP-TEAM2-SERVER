import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    __table_args__ = (
        UniqueConstraint("invite_code", name="uq_rooms_invite_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="방 ID",
    )

    name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="방 이름",
    )

    color: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="방 폴더 색상",
    )

    invite_code: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
        index=True,
        comment="초대 코드",
    )
