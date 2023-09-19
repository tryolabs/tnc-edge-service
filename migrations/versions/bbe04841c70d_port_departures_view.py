"""port_departures_view

Revision ID: bbe04841c70d
Revises: b78dce0f5492
Create Date: 2023-09-19 11:59:42.945969

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbe04841c70d'
down_revision = 'b78dce0f5492'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.get_bind().execute('create table if not exists port_location (port_location point);')
    op.get_bind().execute('truncate port_location;')
    op.get_bind().execute('insert into port_location (port_location) values (point(9.4241879,-84.1833372));')

    op.get_bind().execute("""CREATE OR REPLACE VIEW port_departures as (
with A as (
    select *,
    ( point(lat, lon) <-> port_location.port_location ) < 0.3 at_port,
    row_number() over (order by gps_datetime)
    from gpsdata cross join port_location )
select B.gps_datetime as datetime, B.lat, B.lon from A join A B on a.row_number = b.row_number-1
where a.at_port = true and b.at_port = false);""")


def downgrade() -> None:
    op.get_bind().execute('drop view port_departures;')
    op.get_bind().execute('drop table port_location;')
