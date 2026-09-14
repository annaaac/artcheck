"""enable sqlite autoincrement on artworks and similar_artworks

Revision ID: aaa961b79449
Revises: ba2b1165c531
Create Date: 2026-09-13 17:31:14.304785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aaa961b79449'
down_revision: Union[str, Sequence[str], None] = 'ba2b1165c531'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('artworks', recreate='always', table_kwargs={'sqlite_autoincrement': True}) as batch_op:
        pass

    with op.batch_alter_table('similar_artworks', recreate='always', table_kwargs={'sqlite_autoincrement': True}) as batch_op:
        pass


def downgrade() -> None:
    with op.batch_alter_table('artworks', recreate='always', table_kwargs={}) as batch_op:
        pass

    with op.batch_alter_table('similar_artworks', recreate='always', table_kwargs={}) as batch_op:
        pass