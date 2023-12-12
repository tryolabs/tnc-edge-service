"""refactor_aifish

Revision ID: 5fdb864a1bbb
Revises: e718ddd7c0bd
Create Date: 2023-12-12 12:43:34.309532

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5fdb864a1bbb'
down_revision = 'e718ddd7c0bd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    op.create_table('aifishdata',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('video_uri', sa.String(), nullable=True),
    sa.Column('processing_uri', sa.String(), nullable=True),
    sa.Column('output_uri', sa.String(), nullable=True),
    sa.Column('datetime', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.Column('runtimems', sa.REAL(), nullable=True),
    sa.Column('detection_confidence', sa.REAL(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['video_uri'], ['video_files.decrypted_path'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('video_uri')
    )
    op.drop_table('fishaidata')
    


def downgrade() -> None:
    op.create_table('fishaidata',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('video_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('cocoannotations_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('datetime', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='fishaidata_pkey')
    )
    op.drop_table('aifishdata')
