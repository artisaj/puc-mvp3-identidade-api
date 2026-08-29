"""Create sessions table.

Revision ID: 20260829_0003
Revises: 20260829_0002
Create Date: 2026-08-29
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260829_0003"
down_revision: Union[str, Sequence[str], None] = "20260829_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria as sessões vinculadas a usuários."""
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])


def downgrade() -> None:
    """Remove a tabela de sessões."""
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
