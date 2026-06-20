"""add_compliance_fields

Revision ID: 002
Revises: 001
Create Date: 2026-06-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001' # Assumes 001 exists as base
branch_labels = None
depends_on = None

def upgrade():
    # Add new compliance fields to the donations table
    op.add_column('donations', sa.Column('packaging_type', sa.String(), nullable=True))
    op.add_column('donations', sa.Column('storage_temp', sa.String(), nullable=True))
    op.add_column('donations', sa.Column('allergen_tags', postgresql.ARRAY(sa.String()), nullable=True))

def downgrade():
    # Remove compliance fields
    op.drop_column('donations', 'allergen_tags')
    op.drop_column('donations', 'storage_temp')
    op.drop_column('donations', 'packaging_type')
