"""ondeckdata_more_data_columns

Revision ID: ba08d4e11cc7
Revises: 495235ece5f0
Create Date: 2023-10-11 17:33:42.633350

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ba08d4e11cc7'
down_revision = '495235ece5f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('ondeckdata', sa.Column('overallcatches', sa.Integer(), nullable=True))
    op.add_column('ondeckdata', sa.Column('overalldiscards', sa.Integer(), nullable=True))
    op.add_column('ondeckdata', sa.Column('detection_confidence', sa.REAL(), nullable=True))



def downgrade() -> None:
    op.drop_column('ondeckdata', 'detection_confidence')
    op.drop_column('ondeckdata', 'overalldiscards')
    op.drop_column('ondeckdata', 'overallcatches')


