"""ondeck_json_columns

Revision ID: b78dce0f5492
Revises: 643148911953
Create Date: 2023-08-16 14:16:31.080353

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b78dce0f5492'
down_revision = '643148911953'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.add_column('ondeckdata', sa.Column('overallcount', sa.Integer(), nullable=True))
    op.add_column('ondeckdata', sa.Column('overallruntimems', sa.REAL(), nullable=True))
    op.add_column('ondeckdata', sa.Column('tracked_confidence', sa.REAL(), nullable=True))


    op.create_unique_constraint('uq_video_files_decrypted_path', 'video_files', ['decrypted_path'])
    
    op.get_bind().execute('delete from ondeckdata where id in (select ondeckdata.id from ondeckdata left join video_files on video_uri = decrypted_path where decrypted_path is null);')
    op.create_foreign_key(None, 'ondeckdata', 'video_files', ['video_uri'], ['decrypted_path'])



def downgrade() -> None:
    op.drop_constraint(None, 'ondeckdata', type_='foreignkey')
    op.drop_constraint('uq_video_files_decrypted_path', 'video_files', type_='unique')
    op.drop_column('ondeckdata', 'tracked_confidence')
    op.drop_column('ondeckdata', 'overallruntimems')
    op.drop_column('ondeckdata', 'overallcount')

