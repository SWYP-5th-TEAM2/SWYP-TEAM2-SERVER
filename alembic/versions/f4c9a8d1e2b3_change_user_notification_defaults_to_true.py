"""change user notification defaults to true

Revision ID: f4c9a8d1e2b3
Revises: c9e8b7a6d5f4
Create Date: 2026-07-26 00:00:00.000000+09:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c9a8d1e2b3"
down_revision: Union[str, None] = "c9e8b7a6d5f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NOTIFICATION_SETTING_COLUMNS = (
    "candidate_place_enabled",
    "vote_deadline_enabled",
    "schedule_confirmed_enabled",
    "quiet_recommendation_enabled",
)


def upgrade() -> None:
    for column_name in NOTIFICATION_SETTING_COLUMNS:
        op.alter_column(
            "users",
            column_name,
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.text("true"),
        )


def downgrade() -> None:
    for column_name in NOTIFICATION_SETTING_COLUMNS:
        op.alter_column(
            "users",
            column_name,
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.text("false"),
        )
