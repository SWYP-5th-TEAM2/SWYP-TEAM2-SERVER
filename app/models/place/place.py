import uuid

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin
from app.models.place.enums import PlaceStatus


class Place(Base, TimestampMixin):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="후보 장소 ID",
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="방 ID",
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
        comment="장소를 등록한 사용자 ID",
    )

    place_image_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("images.id", ondelete="SET NULL"),
        nullable=True,
        comment="장소 썸네일 이미지 ID",
    )

    source_image_id: Mapped[uuid.UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("images.id", ondelete="SET NULL"),
        nullable=True,
        comment="소스 이미지 ID",
    )

    status: Mapped[PlaceStatus] = mapped_column(
        Enum(PlaceStatus, name="place_status"),
        nullable=False,
        default=PlaceStatus.READY_TO_DRAW,
        server_default=PlaceStatus.READY_TO_DRAW.value,
        comment="장소 상태",
    )

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="후보 타이틀",
    )

    name: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="장소명",
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="장소 위치",
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="장소 위도",
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="장소 경도",
    )

    memo: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="메모",
    )

    place_image: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="장소 썸네일 이미지 URL",
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="정보 출처",
    )

    url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="출처 URL",
    )
