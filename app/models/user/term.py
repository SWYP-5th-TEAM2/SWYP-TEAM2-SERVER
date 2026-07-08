import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.database.base import Base
from app.models.mixins import TimestampMixin
from app.models.user.enums import TermType


class Term(Base, TimestampMixin):
    __tablename__ = "terms"

    id: Mapped[uuid.UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        comment="약관 ID",
    )

    type: Mapped[TermType] = mapped_column(
        Enum(TermType, name="term_type"),
        nullable=False,
        comment="약관 유형",
    )

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="약관 타이틀",
    )

    version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="v1.0",
        server_default="v1.0",
        comment="약관 버전",
    )

    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="필수 동의 여부",
    )

    content_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="약관 본문 URL",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="활성 여부",
    )

    effective_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="약관 적용 시작일",
    )
