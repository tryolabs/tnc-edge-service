"""add_elog_timegap_vector_row

Revision ID: fdfd9e708602
Revises: ba08d4e11cc7
Create Date: 2023-11-07 16:50:44.303059

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fdfd9e708602'
down_revision = 'ba08d4e11cc7'
branch_labels = None
depends_on = None

   
def upgrade() -> None:
    # stmt = sa.select(sa.table('vectors')).where(name="ElogTimeGapsVector")
    found_id = None
    for row in op.get_bind().execute("select id, name from vectors where name = 'ElogTimeGapsVector';"):
        if row:
            found_id = row[0]
    
    if found_id is None:
        op.get_bind().execute('insert into vectors (name, configblob, schedule_string) values (\'ElogTimeGapsVector\', \'{}\', \'every 4 hours\');')
    
    


def downgrade() -> None:
    op.get_bind().execute("delete from tests where vector_id = (select id from vectors where name = 'ElogTimeGapsVector');");

    t = sa.table('vectors')
    op.get_bind().execute("delete from vectors where name = 'ElogTimeGapsVector';")

