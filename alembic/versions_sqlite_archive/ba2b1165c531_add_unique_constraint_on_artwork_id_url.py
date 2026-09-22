"""add unique constraint on artwork_id, url

Revision ID: ba2b1165c531
Revises: 7d2e189fd626
Create Date: 2026-08-28 00:30:54.641353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba2b1165c531'
down_revision: Union[str, Sequence[str], None] = '7d2e189fd626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('similar_artworks') as batch_op:
        batch_op.create_unique_constraint('uq_artwork_url', ['artwork_id', 'url'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('similar_artworks') as batch_op:
        batch_op.drop_constraint('uq_artwork_url', type_='unique')