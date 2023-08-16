"""deckhand json views

Revision ID: 643148911953
Revises: 677a2f2884e1
Create Date: 2023-08-16 11:38:18.120705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '643148911953'
down_revision = '677a2f2884e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute("""
        CREATE OR REPLACE VIEW deckhandevents_mostrecenteventid_nophoto AS 
        SELECT a.id, a.jsonblob::jsonb - 'gearPhoto' AS jsonblob,  a.datetime
        FROM deckhandevents a
        JOIN (
            SELECT max(id) AS id 
            FROM deckhandevents b 
            GROUP BY b.jsonblob::jsonb->'eventId'
        ) c ON a.id = c.id;
    """)

    op.get_bind().execute("""
        CREATE OR REPLACE VIEW deckhandevents_mostrecentlonglineevent_jsonextracted AS
        SELECT a.id, a.jsonblob, a.datetime,
            jsonb_array_length(a.jsonblob->'bycatch') AS bycatchcount,
            sum((b.catchcount->'amount')::integer) AS catchcount,
            TO_TIMESTAMP((jsonblob->'locationData'->'systemStartSetDateTime')::decimal) AS systemstartsetdatetime,
            (jsonblob->'locationData'->'systemStartSetLatitude')::decimal AS systemstartsetlatitude,
            (jsonblob->'locationData'->'systemStartSetLongitude')::decimal AS systemstartsetlongitude,
            TO_TIMESTAMP((jsonblob->'locationData'->'systemEndSetDateTime')::decimal) AS systemendsetdatetime,
            (jsonblob->'locationData'->'systemEndSetLatitude')::decimal AS systemendsetlatitude,
            (jsonblob->'locationData'->'systemEndSetLongitude')::decimal AS systemendsetlongitude,
            TO_TIMESTAMP((jsonblob->'locationData'->'systemStartHaulDateTime')::decimal) AS systemstarthauldatetime,
            (jsonblob->'locationData'->'systemStartHaulLatitude')::decimal AS systemstarthaullatitude,
            (jsonblob->'locationData'->'systemStartHaulLongitude')::decimal AS systemstarthaullongitude,
            TO_TIMESTAMP((jsonblob->'locationData'->'systemEndHaulDateTime')::decimal) AS systemendhauldatetime,
            (jsonblob->'locationData'->'systemEndHaulLatitude')::decimal AS systemendhaullatitude,
            (jsonblob->'locationData'->'systemEndHaulLongitude')::decimal AS systemendhaullongitude
        FROM deckhandevents_mostrecenteventid_nophoto a,
        LATERAL jsonb_array_elements(jsonblob->'catch') AS b(catchcount)
        WHERE a.jsonblob->>'eventType' = 'longlineEvent'
        GROUP BY a.id,  a.jsonblob, a.datetime, bycatchcount;
    """)
    


def downgrade() -> None:
    op.get_bind().execute('DROP VIEW deckhandevents_mostrecentlonglineevent_jsonextracted;')
    op.get_bind().execute('DROP VIEW deckhandevents_mostrecenteventid_nophoto;')
    pass
