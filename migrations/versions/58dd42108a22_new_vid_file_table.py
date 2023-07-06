"""new_vid_file_table

Revision ID: 58dd42108a22
Revises: f9dbf07180af
Create Date: 2023-06-16 18:15:23.314916

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58dd42108a22'
down_revision = 'f9dbf07180af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('video_files',
    sa.Column('original_path', sa.String(), nullable=False),
    sa.Column('last_modified', sa.DateTime(timezone=True), nullable=False),
    sa.Column('decrypted_path', sa.String(), nullable=True),
    sa.Column('decrypted_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('stdout', sa.String(), nullable=True),
    sa.Column('stderr', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('original_path')
    )
    pass


def downgrade() -> None:
    op.drop_table('video_files')
