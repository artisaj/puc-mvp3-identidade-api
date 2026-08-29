"""Initial database revision.

Revision ID: 20260829_0001
Revises:
Create Date: 2026-08-29
"""

from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = "20260829_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Estabelece a revisão inicial sem tabelas de domínio."""


def downgrade() -> None:
    """Remove a revisão inicial sem tabelas de domínio."""
