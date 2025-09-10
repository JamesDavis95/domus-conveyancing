"""ensure required columns exist

Revision ID: 20250910_02
Revises: 20250910_01
Create Date: 2025-09-10 00:05:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '20250910_02'
down_revision = '20250910_01'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('matters') as batch:
        batch.add_column(sa.Column('council_id', sa.String(length=64), nullable=True))
        batch.add_column(sa.Column('status', sa.String(length=32), nullable=True, server_default='done'))
    with op.batch_alter_table('findings') as batch:
        batch.add_column(sa.Column('evidence_json', sa.Text(), nullable=True))
    with op.batch_alter_table('risks') as batch:
        batch.add_column(sa.Column('evidence_json', sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table('risks') as batch:
        batch.drop_column('evidence_json')
    with op.batch_alter_table('findings') as batch:
        batch.drop_column('evidence_json')
    with op.batch_alter_table('matters') as batch:
        batch.drop_column('status')
        batch.drop_column('council_id')
