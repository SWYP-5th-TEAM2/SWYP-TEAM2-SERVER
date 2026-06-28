import uuid

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.image.enums import ImagePurpose
from app.models.mixins import TimestampMixin


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="이미지 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="업로드 사용자 ID",
    )

    image_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="이미지 저장 URL",
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="이미지 파일명",
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="이미지 파일 크기(byte)",
    )

    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="이미지 파일 형식",
    )

    image_purpose: Mapped[ImagePurpose] = mapped_column(
        Enum(ImagePurpose, name="image_purpose"),
        nullable=False,
        default=ImagePurpose.ETC,
        comment="이미지 사용 목적",
    )
