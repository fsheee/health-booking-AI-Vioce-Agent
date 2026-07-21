"""add approval_requests table and patients.is_vip for HITL workflow

Revision ID: a1c9f3d47b21
Revises: e796b859069d
Create Date: 2026-07-19 21:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = 'a1c9f3d47b21'
down_revision: Union[str, None] = 'e796b859069d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

approval_request_type = sa.Enum(
    'emergency_escalation',
    'urgent_symptoms',
    'late_cancellation',
    'vip_request',
    'manual_doctor_assignment',
    'double_booking',
    'low_confidence',
    'appointment_booking',
    'other',
    name='approvalrequesttype',
)
approval_status = sa.Enum('pending', 'approved', 'rejected', name='approvalstatus')


def upgrade() -> None:
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.Uuid(), nullable=True),
        sa.Column('appointment_id', sa.Uuid(), nullable=True),
        sa.Column('request_type', approval_request_type, nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('requested_action', sa.JSON(), nullable=True),
        sa.Column('status', approval_status, nullable=False),
        sa.Column('approved_by', sa.Uuid(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewer_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_approval_requests_org_id', 'approval_requests', ['org_id'])
    op.create_index('ix_approval_requests_patient_id', 'approval_requests', ['patient_id'])
    op.create_index('ix_approval_requests_status', 'approval_requests', ['status'])

    op.add_column(
        'patients',
        sa.Column('is_vip', sa.Boolean(), server_default='false', nullable=False),
    )


def downgrade() -> None:
    op.drop_column('patients', 'is_vip')
    op.drop_index('ix_approval_requests_status', table_name='approval_requests')
    op.drop_index('ix_approval_requests_patient_id', table_name='approval_requests')
    op.drop_index('ix_approval_requests_org_id', table_name='approval_requests')
    op.drop_table('approval_requests')
    approval_request_type.drop(op.get_bind(), checkfirst=True)
    approval_status.drop(op.get_bind(), checkfirst=True)
