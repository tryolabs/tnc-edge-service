"""elog_gaps_score_update

Revision ID: d974c1aea745
Revises: b2f76c38a4a0
Create Date: 2023-09-19 13:16:37.865465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd974c1aea745'
down_revision = 'b2f76c38a4a0'
branch_labels = None
depends_on = None



def upgrade() -> None:
    op.get_bind().execute("""CREATE OR REPLACE VIEW elog_time_gap_score as (
with paired_seq_deckhandevents as (
    with A as (
        select 
            row_number() OVER (order by systemendhauldatetime asc),
            systemendhauldatetime,
            is_arrival_event 
        from (
            select 
                systemendhauldatetime as systemendhauldatetime,
                false as is_arrival_event
            from deckhandevents_mostrecentlonglineevent_jsonextracted 
            union 
            select 
                datetime as systemendhauldatetime,
                false as is_arrival_event
            from port_departures
            union 
            select 
                datetime as systemendhauldatetime,
                true as is_arrival_event
            from port_arrivals
        ) hauls_and_departures
    )
    select A.systemendhauldatetime ts_prev, 
        coalesce(B.systemendhauldatetime, current_timestamp) ts_next , 
        coalesce(B.systemendhauldatetime, current_timestamp) - A.systemendhauldatetime ts_diff
    from A left join A B on a.row_number = b.row_number-1
    where not a.is_arrival_event
)
select *, elog_time_gap_sigmoid(extract(epoch from ts_diff)/3600) score from paired_seq_deckhandevents );
""")


def downgrade() -> None:
    pass