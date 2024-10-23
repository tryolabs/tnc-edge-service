import io
import os
import string
import time
from datetime import datetime, timedelta, timezone

import boto3
import click
import psycopg2
import schedule
from flask.config import Config as FlaskConfig
from psycopg2.pool import SimpleConnectionPool
from sqlalchemy.orm import Session

from model import Test

flaskconfig = FlaskConfig(root_path="")

flaskconfig.from_object("config.defaults")
if "ENVIRONMENT" in os.environ:
    flaskconfig.from_envvar("ENVIRONMENT")


s3 = boto3.resource("s3")
bucket = s3.Bucket("51-gema-dev-dp-raw")


csvprintable = string.printable
csvprintable = csvprintable[0 : 1 + csvprintable.index("\t")]
csvprintable = csvprintable.replace(",", "")


def csvfilter(s):
    return "".join(filter(lambda c: c in csvprintable, s))


def DEPRECATED_export_method_with_sqlalchemy_models(session: Session):
    try:
        now = datetime.now().astimezone(timezone.utc)

        result = (
            session.query(Test)
            .where(Test.datetime_from > now - timedelta(days=13), Test.vector_id == 2)
            .order_by(Test.datetime.desc())
            .limit(1)
            .all()
        )
        rows = list(result)
        if len(rows) > 0:
            partition = str(now.year) + "/" + str(now.month) + "/" + str(now.day)

            body = io.BytesIO()
            body.write(
                (",".join([column.name for column in Test.__mapper__.columns]) + "\n").encode()
            )
            [
                body.write(
                    (
                        ",".join(
                            [str(getattr(row, column.name)) for column in Test.__mapper__.columns]
                        )
                        + "\n"
                    ).encode()
                )
                for row in rows
            ]
            bucket.put_object(
                Key="tnc_edge/"
                + Test.__tablename__
                + "/"
                + partition
                + "/"
                + str(int(now.timestamp()))
                + ".csv",
                Body=body.getvalue(),
            )
    except Exception as e:
        print("Error: exception in s3 uploader", e)


def DEPRECATED_s3uploader(cpool: SimpleConnectionPool, boat, ver):
    DEPRECATED_tables = [
        "deckhandevents",
        "gpsdata",
        "internetdata",
        "deckhandevents_mostrecentlonglineevent_jsonextracted",
        "tests",
        "video_files",
        "tracks",
        "ondeckdata",
        "aifishdata",
    ]

    conn: psycopg2.connection = cpool.getconn()
    try:
        with conn.cursor() as cur:
            for table in DEPRECATED_tables:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns \
                            WHERE table_name = %s order by ordinal_position;",
                    (table,),
                )
                columns = cur.fetchall()

                cur.execute(
                    "select max(a.max), CURRENT_TIMESTAMP from ( \
                                select max(s3uploads.datetime), CURRENT_TIMESTAMP \
                                from s3uploads where tablename = %s group by tablename \
                                union select timestamp with time zone '1970-01-01' as max, CURRENT_TIMESTAMP \
                            ) a;",
                    (table,),
                )
                dates = cur.fetchone()

                if table == "video_files":
                    cur.execute(
                        "select * from video_files where start_datetime > %s and start_datetime <= %s;",
                        (dates[0], dates[1]),
                    )
                else:
                    cur.execute(
                        "select * from " + table + " where datetime > %s and datetime <= %s;",
                        (dates[0], dates[1]),
                    )

                now = datetime.now().astimezone(timezone.utc)
                partition = str(now.year) + "/" + str(now.month) + "/" + str(now.day)

                rows = list(cur.fetchall())
                if len(rows) > 0:
                    body = io.BytesIO()
                    body.write((",".join([column[0] for column in columns]) + "\n").encode())
                    [
                        body.write(
                            (",".join([csvfilter(str(value)) for value in row]) + "\n").encode()
                        )
                        for row in rows
                    ]

                    bucket.put_object(
                        Key="tnc_edge/"
                        + boat
                        + "_"
                        + ver
                        + "_"
                        + table
                        + "/"
                        + partition
                        + "/"
                        + str(int(dates[1].timestamp()))
                        + ".csv",
                        Body=body.getvalue(),
                    )

                cur.execute(
                    "insert into s3uploads (datetime, tablename) values (%s, %s)",
                    (
                        dates[1],
                        table,
                    ),
                )
                conn.commit()
    finally:
        cpool.putconn(conn)


def s3psqlcopyer(cpool: SimpleConnectionPool, boat, ver):
    tables = [
        "deckhandevents",
        "gpsdata",
        "internetdata",
        "deckhandevents_mostrecentlonglineevent_jsonextracted",
        "tests",
        "video_files",
        "tracks",
        "ondeckdata",
        "aifishdata",
    ]

    conn: psycopg2.connection = cpool.getconn()

    try:
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns \
                            WHERE table_name = %s order by ordinal_position;",
                    (table,),
                )
                columns = cur.fetchall()

                cur.execute(
                    "select max(a.max), CURRENT_TIMESTAMP from ( \
                                select max(s3uploads.datetime), CURRENT_TIMESTAMP \
                                from s3uploads where tablename = %s group by tablename \
                                union select timestamp with time zone '1970-01-01' as max, CURRENT_TIMESTAMP \
                            ) a;",
                    (table,),
                )
                dates = cur.fetchone()

                cur.execute(f"CREATE TEMP TABLE t as SELECT * from {table} where false;")

                if table == "video_files":
                    cur.execute(
                        f"insert into t (select * from video_files where start_datetime > '{dates[0]}' and start_datetime <= '{dates[1]}');"
                    )
                else:
                    cur.execute(
                        f"insert into t (select * from {table} where datetime > '{dates[0]}' and datetime <= '{dates[1]}');"
                    )
                copy_sql = f"COPY t TO STDOUT WITH CSV HEADER;"
                now = datetime.now().astimezone(timezone.utc)
                partition = str(now.year) + "/" + str(now.month) + "/" + str(now.day)

                f = io.BytesIO()
                cur.copy_expert(copy_sql, f)
                f.seek(0)
                f.readline()  # csv header line
                if len(f.readline()) > 0:  # first line of data. If it exists, write to bucket
                    f.seek(0)
                    key = (
                        "tnc_edge/"
                        + boat
                        + "_"
                        + ver
                        + "_"
                        + table
                        + "/"
                        + partition
                        + "/"
                        + str(int(dates[1].timestamp()))
                        + ".csv"
                    )
                    click.echo(f"uploading {key}")
                    bucket.put_object(Key=key, Body=f.getvalue())

                cur.execute(
                    "insert into s3uploads (datetime, tablename) values (%s, %s)",
                    (
                        dates[1],
                        table,
                    ),
                )
                cur.execute("drop table t;")
                conn.commit()
    finally:
        cpool.putconn(conn)


@click.command()
@click.option("--dbname", default=flaskconfig.get("DBNAME"))
@click.option("--dbuser", default=flaskconfig.get("DBUSER"))
@click.option("--boatname", default=flaskconfig.get("BOAT_NAME"))
@click.option("--dbtablesversion", default=flaskconfig.get("DB_TABLES_VERSION"))
@click.option("--test", is_flag=True)
def main(dbname, dbuser, boatname, dbtablesversion, test):
    # engine = create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    # SessionMaker = sessionmaker(engine)
    # ModelBase.metadata.create_all(engine)

    cpool = SimpleConnectionPool(1, 1, database=dbname, user=dbuser)

    if test:
        # s3psqlcopyer(cpool, boatname, dbtablesversion)

        return

    def runonce(cpool, boatname, dbtablesversion):
        s3psqlcopyer(cpool, boatname, dbtablesversion)
        return schedule.CancelJob

    schedule.every(1).seconds.do(runonce, cpool, boatname, dbtablesversion)
    schedule.every(1).hours.do(s3psqlcopyer, cpool, boatname, dbtablesversion)

    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            click.echo(f"sleeping for: {n}")
            time.sleep(n)
        schedule.run_pending()


if __name__ == "__main__":
    main()
