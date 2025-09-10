"""baseline tables

Revision ID: 20250910_01
Revises:
Create Date: 2025-09-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250910_01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('matters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.String(length=64), nullable=True),
        sa.Column('council_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='done'),
    )
    op.create_table('findings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('matter_id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=255), nullable=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('evidence_json', sa.Text(), nullable=True),
    )
    op.create_foreign_key('fk_findings_matter', 'findings', 'matters', ['matter_id'], ['id'])
    op.create_table('risks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('matter_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=True),
        sa.Column('level', sa.String(length=32), nullable=True),
        sa.Column('evidence_json', sa.Text(), nullable=True),
    )
    op.create_foreign_key('fk_risks_matter', 'risks', 'matters', ['matter_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_risks_matter', 'risks', type_='foreignkey')
    op.drop_table('risks')
    op.drop_constraint('fk_findings_matter', 'findings', type_='foreignkey')
    op.drop_table('findings')
    op.drop_table('matters')
