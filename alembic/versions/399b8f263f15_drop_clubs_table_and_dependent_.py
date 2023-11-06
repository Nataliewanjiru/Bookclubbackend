"""Drop clubs table and dependent constraints

Revision ID: 399b8f263f15
Revises: f3879208fcd2
Create Date: 2023-11-06 18:03:28.910001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '399b8f263f15'
down_revision: Union[str, None] = 'f3879208fcd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     op.execute("ALTER TABLE clubusers DROP CONSTRAINT IF EXISTS clubusers_clubID_fkey")
     op.execute("ALTER TABLE reviews DROP CONSTRAINT IF EXISTS reviews_clubID_fkey")
     op.execute("ALTER TABLE books DROP CONSTRAINT IF EXISTS books_clubID_fkey")




     op.drop_table('clubs')

def downgrade() -> None:
    pass
