"""add_track_table

Revision ID: e718ddd7c0bd
Revises: fdfd9e708602
Create Date: 2023-12-05 16:55:46.938879

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e718ddd7c0bd'
down_revision = 'fdfd9e708602'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table('tracks',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('video_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('cocoannotations_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('track_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('first_framenum', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('last_framenum', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('confidences', postgresql.ARRAY(sa.REAL()), autoincrement=False, nullable=True),
    sa.Column('datetime', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='tracks_pkey')
    )


def downgrade() -> None:
    op.drop_table('tracks')

