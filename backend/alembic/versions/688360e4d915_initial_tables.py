"""initial tables

Revision ID: 688360e4d915
Revises: 
Create Date: 2026-07-11 03:26:09.212357
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = '688360e4d915'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('organizations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)

    op.create_table('users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(10), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_org_id', 'users', ['org_id'])

    op.create_table('audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.Uuid(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_audit_logs_org_id', 'audit_logs', ['org_id'])

    op.create_table('doctors',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('specialization', sa.String(255), nullable=True),
        sa.Column('license_number', sa.String(100), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
    )
    op.create_index('ix_doctors_org_id', 'doctors', ['org_id'])

    op.create_table('patients',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('medical_history', sa.Text(), nullable=True),
        sa.Column('emergency_contact', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
    )
    op.create_index('ix_patients_org_id', 'patients', ['org_id'])

    op.create_table('appointments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.Uuid(), nullable=False),
        sa.Column('doctor_id', sa.Uuid(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(9), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id']),
    )
    op.create_index('ix_appointments_org_id', 'appointments', ['org_id'])
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
    op.create_index('ix_appointments_doctor_id', 'appointments', ['doctor_id'])

    op.create_table('voice_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('transcription', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('actions_taken', sa.JSON(), nullable=True),
        sa.Column('is_emergency', sa.Boolean(), nullable=False),
        sa.Column('escalated_to_human', sa.Boolean(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_voice_sessions_org_id', 'voice_sessions', ['org_id'])
    op.create_index('ix_voice_sessions_patient_id', 'voice_sessions', ['patient_id'])

    op.create_table('reminders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('org_id', sa.Uuid(), nullable=False),
        sa.Column('appointment_id', sa.Uuid(), nullable=True),
        sa.Column('patient_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(11), nullable=False),
        sa.Column('channel', sa.String(5), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(9), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
    )
    op.create_index('ix_reminders_org_id', 'reminders', ['org_id'])
    op.create_index('ix_reminders_patient_id', 'reminders', ['patient_id'])


def downgrade() -> None:
    op.drop_table('reminders')
    op.drop_table('voice_sessions')
    op.drop_table('appointments')
    op.drop_table('patients')
    op.drop_table('doctors')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('organizations')
