from alembic import op
import sqlalchemy as sa

revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('matters',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('ref', sa.String(255)),
        sa.Column('created_at', sa.String(64)),
        sa.Column('council_id', sa.String(64), nullable=True),
        sa.Column('status', sa.String(32), server_default='done')
    )
    op.create_table('findings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('matter_id', sa.Integer, sa.ForeignKey('matters.id')),
        sa.Column('kind', sa.String(255)),
        sa.Column('value', sa.Text),
        sa.Column('evidence_json', sa.Text, nullable=True),
    )
    op.create_table('risks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('matter_id', sa.Integer, sa.ForeignKey('matters.id')),
        sa.Column('code', sa.String(255)),
        sa.Column('level', sa.String(32)),
        sa.Column('evidence_json', sa.Text, nullable=True),
    )

def downgrade():
    op.drop_table('risks')
    op.drop_table('findings')
    op.drop_table('matters')
