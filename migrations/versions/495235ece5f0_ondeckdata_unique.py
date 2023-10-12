"""ondeckdata_unique

Revision ID: 495235ece5f0
Revises: f48359cf7456
Create Date: 2023-10-10 15:43:07.752816

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '495235ece5f0'
down_revision = 'f48359cf7456'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.execute("""
               with duped as (
                select distinct on (video_uri) video_uri, id 
                from ondeckdata 
                order by video_uri, datetime desc
               ) 
               delete from ondeckdata 
               where video_uri in (select video_uri from duped) 
               and id not in (select id from duped)
               ;""")
    op.create_unique_constraint(None, 'ondeckdata', ['video_uri'])
    


def downgrade() -> None:
    op.drop_constraint(None, 'ondeckdata', type_='unique')
