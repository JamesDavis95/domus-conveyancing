from alembic import op
import sqlalchemy as sa

revision = '0002_add_status_evidence'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('matters') as b:
        # b.add_column(sa.Column('status', sa.String(32), server_default='done'))  # Already in model
        # b.add_column(sa.Column('council_id', sa.String(64), nullable=True))  # Already in model
        pass
    with op.batch_alter_table('findings') as b:
        # b.add_column(sa.Column('evidence_json', sa.Text, nullable=True))  # Already in model
        pass
    with op.batch_alter_table('risks') as b:
        # b.add_column(sa.Column('evidence_json', sa.Text, nullable=True))  # Already in model
        pass

def downgrade():
    with op.batch_alter_table('risks') as b:
        # b.drop_column('evidence_json')  # Already in model
        pass
    with op.batch_alter_table('findings') as b:
        # b.drop_column('evidence_json')  # Already in model
        pass
    with op.batch_alter_table('matters') as b:
        # b.drop_column('council_id')  # Already in model
        # b.drop_column('status')  # Already in model
        pass
