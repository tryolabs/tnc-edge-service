"""reencode_files

Revision ID: 8304966281aa
Revises: d974c1aea745
Create Date: 2023-09-20 15:15:56.043600

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8304966281aa'
down_revision = 'd974c1aea745'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('video_files', sa.Column('reencoded_path', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('video_files', sa.Column('reencoded_datetime', sa.DateTime(timezone=True), autoincrement=False, nullable=True))
    op.add_column('video_files', sa.Column('reencoded_stdout', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('video_files', sa.Column('reencoded_stderr', sa.VARCHAR(), autoincrement=False, nullable=True))


def downgrade() -> None:
    op.drop_column('video_files', 'reencoded_stderr')
    op.drop_column('video_files', 'reencoded_stdout')
    op.drop_column('video_files', 'reencoded_datetime')
    op.drop_column('video_files', 'reencoded_path')
