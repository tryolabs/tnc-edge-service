"""new_vector_rows_1

Revision ID: 17911f3ffb3b
Revises: f835aa8c569a
Create Date: 2023-06-02 14:22:38.910122

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17911f3ffb3b'
down_revision = 'f835aa8c569a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # stmt = sa.select(sa.table('vectors')).where(name="InternetVector")
    found_id = None
    for row in op.get_bind().execute("select id, name from vectors where name = 'InternetVector';"):
        if row:
            found_id = row[0]
    
    if found_id is None:
        op.get_bind().execute('insert into vectors (name, configblob) values (\'InternetVector\', \'{"target_ips":["8.8.8.8","1.1.1.1","208.67.222.222","9.9.9.9"],"run_traceroute":false}\');')
    
    


def downgrade() -> None:
    
    op.get_bind().execute("delete from tests where vector_id = (select id from vectors where name = 'InternetVector');");

    t = sa.table('vectors')
    op.get_bind().execute("delete from vectors where name = 'InternetVector';")


