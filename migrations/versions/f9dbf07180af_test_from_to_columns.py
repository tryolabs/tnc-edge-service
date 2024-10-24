"""test_from_to_columns

Revision ID: f9dbf07180af
Revises: 47ff3fca73a4
Create Date: 2023-06-06 13:12:18.789652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9dbf07180af'
down_revision = '47ff3fca73a4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tests', sa.Column('datetime_from', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tests', sa.Column('datetime_to', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tests', 'datetime_to')
    op.drop_column('tests', 'datetime_from')
    # ### end Alembic commands ###
