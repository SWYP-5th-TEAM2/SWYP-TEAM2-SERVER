"""allow null place user

Revision ID: 4c6f8b2e1a90
Revises: 9bfc3a3c583a
Create Date: 2026-06-29 00:00:00.000000+09:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4c6f8b2e1a90"
down_revision: Union[str, None] = "9bfc3a3c583a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "places_user_id_fkey",
        "places",
        type_="foreignkey",
    )
    op.alter_column(
        "places",
        "user_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_places_user_id_users",
        "places",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_places_user_id_users",
        "places",
        type_="foreignkey",
    )
    op.alter_column(
        "places",
        "user_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.create_foreign_key(
        "places_user_id_fkey",
        "places",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
