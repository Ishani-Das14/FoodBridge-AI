"""add_emergency

Revision ID: 003
Revises: 002
Create Date: 2026-06-22 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('ngo_profiles', sa.Column('ngo_type', sa.String(), server_default='standard', nullable=False))
    
    op.create_table('emergency_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('affected_districts', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('triggered_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('emergency_logs')
    op.drop_column('ngo_profiles', 'ngo_type')
