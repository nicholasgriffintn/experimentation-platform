"""Adding traffic allocation column

Revision ID: 67c12f835727
Revises: cc2dc1913bf0
Create Date: 2025-02-09 01:25:34.684836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67c12f835727'
down_revision: Union[str, None] = 'cc2dc1913bf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('experiments', sa.Column('traffic_allocation', sa.Float(), nullable=False, default=100.0))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('experiments', 'traffic_allocation')
    # ### end Alembic commands ###
