from alembic import op
import sqlalchemy as sa

revision = '0002_add_status_evidence'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('matters') as b:
        b.add_column(sa.Column('status', sa.String(32), server_default='done'))
        b.add_column(sa.Column('council_id', sa.String(64), nullable=True))
    with op.batch_alter_table('findings') as b:
        b.add_column(sa.Column('evidence_json', sa.Text, nullable=True))
    with op.batch_alter_table('risks') as b:
        b.add_column(sa.Column('evidence_json', sa.Text, nullable=True))

def downgrade():
    with op.batch_alter_table('risks') as b:
        b.drop_column('evidence_json')
    with op.batch_alter_table('findings') as b:
        b.drop_column('evidence_json')
    with op.batch_alter_table('matters') as b:
        b.drop_column('council_id')
        b.drop_column('status')
