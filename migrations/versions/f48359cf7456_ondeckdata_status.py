"""ondeckdata_status

Revision ID: f48359cf7456
Revises: 8304966281aa
Create Date: 2023-10-09 17:35:01.581320

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f48359cf7456'
down_revision = '8304966281aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    op.add_column('ondeckdata', sa.Column('status', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('ondeckdata', 'status')
