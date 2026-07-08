"""add room member left reason

Revision ID: c9e8b7a6d5f4
Revises: 7ab4b50eae24
Create Date: 2026-07-09 00:00:00.000000+09:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9e8b7a6d5f4"
down_revision: Union[str, None] = "7ab4b50eae24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


room_member_left_reason = sa.Enum(
    "LEFT",
    "KICKED",
    name="room_member_left_reason",
)


def upgrade() -> None:
    room_member_left_reason.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "room_members",
        sa.Column(
            "left_reason",
            room_member_left_reason,
            nullable=True,
            comment="방 나가기 사유",
        ),
    )


def downgrade() -> None:
    op.drop_column("room_members", "left_reason")
    room_member_left_reason.drop(op.get_bind(), checkfirst=True)
