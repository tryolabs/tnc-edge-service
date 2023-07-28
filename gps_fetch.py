
from datetime import datetime,timezone
import click
import codecs
import os
from pathlib import Path
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import re
import schedule
import subprocess
import time


from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')

def thalos_gps_filename_date(filename: str) -> datetime:
    m = re.match('.*(\d{8}).?(\d{6})\.txt', filename)
    if not m:
        return None
    return datetime.fromisoformat(m[1] + " " + m[2] + "+00:00")

def gps_fetch(cpool: SimpleConnectionPool, thalos_dir: Path):

    conn: psycopg2.connection = cpool.getconn()
    gps_files = [x for x in thalos_dir.iterdir()]
    dt_index = {}
    for gps_file in gps_files:
        m = re.match('.*(\d{8}).?(\d{6})\.txt', gps_file.name)
        if not m:
            continue
        dt = datetime.strptime(m[1] + " " + m[2] + "Z", '%Y%m%d %H%M%S%z')
        dt_index[dt] = gps_file

    new_dts = []

    dts_tupled = list(map(lambda x: (x,), dt_index.keys()))
    if len(dts_tupled) > 0:
        try:
            with conn.cursor() as cur:
                args = ','.join(cur.mogrify("(%s)", [dt]).decode('utf-8')
                    for dt in dt_index.keys())
                cur.execute("""WITH t (file_dt) AS ( VALUES """ + args + """ )
                    SELECT t.file_dt FROM t 
                    LEFT JOIN gpsdata ON t.file_dt = gpsdata.gps_datetime
                    WHERE gpsdata.gps_datetime IS NULL;""")
                # print(cur.query)
                # print(cur.description)
                rows = cur.fetchall()
                new_dts.extend(col for cols in rows for col in cols)

            insert_tuples=[]

            for new_dt in new_dts:
                new_file: Path = dt_index[new_dt.astimezone(timezone.utc)]
                with new_file.open() as data:
                    line = data.readline()
                    m = re.match('([+-]?(\d+(\.\d*)?|\.\d+)).*,.*?([+-]?(\d+(\.\d*)?|\.\d+))', line)
                    if m:
                        lat = m[1]
                        lon = m[4]
                        insert_tuples.append((new_dt, lat, lon,))

            if len(insert_tuples) > 0:
                with conn.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO gpsdata (gps_datetime, lat, lon) VALUES (%s, %s, %s);",
                        insert_tuples
                    )
                    # print(cur.query)
                conn.commit()
        finally:
            cpool.putconn(conn)


@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--thalos_gps_dir', default=flaskconfig.get('THALOS_GPS_DIR'))
def main(dbname, dbuser, thalos_gps_dir):

    thalos_gps_dir = Path(thalos_gps_dir)

    cpool = SimpleConnectionPool(1, 1, database=dbname, user=dbuser)
    
    def runonce(cpool, thalos_gps_dir ):
        gps_fetch(cpool, thalos_gps_dir)
        return schedule.CancelJob

    schedule.every(1).seconds.do(runonce, cpool, thalos_gps_dir )
    schedule.every(15).minutes.do(gps_fetch, cpool, thalos_gps_dir )


    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            print("No more jobs. exiting")
            break
        elif n > 0:
            # sleep exactly the right amount of time
            print("sleeping for:", n)
            time.sleep(n)
        schedule.run_pending()

if __name__ == '__main__':
    main()
