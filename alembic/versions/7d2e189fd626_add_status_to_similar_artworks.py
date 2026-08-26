"""add status to similar_artworks

Revision ID: 7d2e189fd626
Revises: 
Create Date: 2026-08-25 20:08:50.789360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d2e189fd626'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'similar_artworks',
        sa.Column('status', sa.String(), nullable=False, server_default='new')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('similar_artworks', 'status')
