"""deckhand_gaps_score

Revision ID: b2f76c38a4a0
Revises: bbe04841c70d
Create Date: 2023-09-19 12:48:47.152161

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2f76c38a4a0'
down_revision = 'bbe04841c70d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute("""create or replace function elog_time_gap_sigmoid(x double precision)
returns double precision
language plpgsql
as
$$
declare
k double precision;
b double precision;
begin
k = -0.15;
b = 60.0;
return 1.0/(1.0+exp(k*(x-b)));
end;
$$;""")


    op.get_bind().execute("""CREATE OR REPLACE VIEW elog_time_gap_score as (
with paired_seq_deckhandevents as (
    with A as (
        select 
            row_number() OVER (order by systemendhauldatetime asc),
            systemendhauldatetime,
            is_haul_event 
        from (
            select 
                systemendhauldatetime as systemendhauldatetime,
                true as is_haul_event
            from deckhandevents_mostrecentlonglineevent_jsonextracted 
            union 
            select 
                datetime as systemendhauldatetime,
                false as is_haul_event
            from port_departures
            union 
            select 
                datetime as systemendhauldatetime,
                false as is_haul_event
            from port_arrivals
        ) hauls_and_departures
    )
    select A.systemendhauldatetime ts_prev, 
        coalesce(B.systemendhauldatetime, current_timestamp) ts_next , 
        coalesce(B.systemendhauldatetime, current_timestamp) - A.systemendhauldatetime ts_diff
    from A left join A B on a.row_number = b.row_number-1
    where not (a.is_haul_event is false and b.is_haul_event is false)
)
select *, elog_time_gap_sigmoid(extract(epoch from ts_diff)/3600) score from paired_seq_deckhandevents );
""")


def downgrade() -> None:
    op.get_bind().execute('drop view elog_time_gap_score');
    op.get_bind().execute('drop function elog_time_gap_sigmoid');
