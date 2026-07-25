"""add org phone address email

Revision ID: 1ac30a41b95d
Revises: a1c9f3d47b21
Create Date: 2026-07-24 02:54:04.257047
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = '1ac30a41b95d'
down_revision: Union[str, None] = 'a1c9f3d47b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('organizations', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('organizations', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('organizations', 'email')
    op.drop_column('organizations', 'address')
    op.drop_column('organizations', 'phone')