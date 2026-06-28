"""add etc to image purpose

Revision ID: a2d280afa318
Revises: 8f0c2b1a7d3e
Create Date: 2026-06-28 20:09:05.836057+09:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a2d280afa318'
down_revision: Union[str, None] = '8f0c2b1a7d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # PostgreSQL Enum 값 추가
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE image_purpose "
            "ADD VALUE IF NOT EXISTS 'ETC'"
        )
    # DB 기본값 설정
    op.alter_column(
        "images",
        "image_purpose",
        server_default=sa.text("'ETC'::image_purpose"),
    )

def downgrade() -> None:
    # 기본값만 제거
    op.alter_column(
        "images",
        "image_purpose",
        server_default=None,
    )