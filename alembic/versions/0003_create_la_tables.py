"""
Alembic migration to create LA tables matching la/models.py
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_create_la_tables'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('la_matters',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('ref', sa.String, nullable=False, unique=True),
        sa.Column('address', sa.String, nullable=True),
        sa.Column('uprn', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )
    op.create_table('la_orders',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('matter_id', sa.String, sa.ForeignKey('la_matters.id'), nullable=False),
        sa.Column('council_code', sa.String, nullable=False),
        sa.Column('types', sa.String, nullable=False),
        sa.Column('provider_ref', sa.String, nullable=True),
        sa.Column('status', sa.String, nullable=False, default='SUBMITTED'),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )
    op.create_table('la_documents',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('order_id', sa.String, sa.ForeignKey('la_orders.id'), nullable=False),
        sa.Column('kind', sa.String, nullable=False),
        sa.Column('file_path', sa.String, nullable=False),
    )
    op.create_table('la_findings',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('matter_id', sa.String, sa.ForeignKey('la_matters.id'), nullable=False),
        sa.Column('kind', sa.String, nullable=False),
        sa.Column('value', sa.Text, nullable=True),
    )
    op.create_table('la_risks',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('matter_id', sa.String, sa.ForeignKey('la_matters.id'), nullable=False),
        sa.Column('code', sa.String, nullable=False),
        sa.Column('level', sa.String, nullable=True),
        sa.Column('evidence_json', sa.Text, nullable=True),
    )

def downgrade():
    op.drop_table('la_risks')
    op.drop_table('la_findings')
    op.drop_table('la_documents')
    op.drop_table('la_orders')
    op.drop_table('la_matters')
