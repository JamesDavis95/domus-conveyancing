"""merge LA and status/evidence branches

Revision ID: d7eff4466045
Revises: 0002_add_status_evidence, 0003_create_la_tables
Create Date: 2025-09-11 13:50:41.856821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7eff4466045'
down_revision: Union[str, Sequence[str], None] = ('0002_add_status_evidence', '0003_create_la_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
