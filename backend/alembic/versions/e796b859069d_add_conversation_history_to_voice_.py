"""add conversation_history to voice_sessions

Revision ID: e796b859069d
Revises: 688360e4d915
Create Date: 2026-07-18 03:23:57.178263
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = 'e796b859069d'
down_revision: Union[str, None] = '688360e4d915'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('voice_sessions', sa.Column('conversation_history', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('voice_sessions', 'conversation_history')
