
import click
import os
from pathlib import Path
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import re
import schedule
import subprocess
from subprocess import CompletedProcess
import time

from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')

class WithableConnection():
    def __init__(self, cpool: SimpleConnectionPool):
        self.cpool: SimpleConnectionPool = cpool
    
    def __enter__(self):
        self.c: psycopg2.connection = self.cpool.getconn()
        return self.c

    def __exit__(self, exception_type, exception_value, traceback):
        self.cpool.putconn(self.c)

def run_ondeck(cpool: SimpleConnectionPool, output_dir: Path):
    
    video_files: list[Path] = []

    with WithableConnection(cpool) as conn:
        with conn.cursor() as cur:
            cur.execute("select video_files.decrypted_path from video_files \
                        left join ondeckdata on video_files.decrypted_path = ondeckdata.video_uri \
                        where video_files.decrypted_path is not null \
                        and ondeckdata.video_uri is null \
                        order by video_files.decrypted_datetime asc;")
            for row in cur:
                video_files.append(Path(row[0]))

    for video_file in video_files:
        last_dot_index: int = video_file.name.index('.')
        if last_dot_index < 0:
            last_dot_index = None
        json_out_file = output_dir / Path(video_file.name[0:last_dot_index] + "_ondeck.json")
        cmd = "sudo /usr/bin/docker run --rm -v /videos:/videos --runtime=nvidia --network none \
                gcr.io/edge-gcr/edge-service-image:latest \
                --output %s --input %s"%(
            str(json_out_file.absolute()), 
            str(video_file.absolute())
            )
        p: CompletedProcess[str] = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if p.returncode == 0:
            with WithableConnection(cpool) as conn:
                with conn.cursor() as cur:
                    cur.execute("insert into ondeckdata ( video_uri, cocoannotations_uri ) \
                                values ( %s, %s ) ;", (
                            str(video_file.absolute()),
                            str(json_out_file.absolute())
                        )
                    )
                conn.commit()
        else:
            print("ondeck model failure. stdout, stderr:", p.stdout, p.stderr)
            with WithableConnection(cpool) as conn:
                with conn.cursor() as cur:
                    cur.execute("insert into ondeckdata ( video_uri, cocoannotations_uri ) \
                                values ( %s, %s ) ;", (
                            str(video_file.absolute()),
                            "ondeck model failure. stdout, stderr: " + p.stdout + p.stderr
                        )
                    )
                conn.commit()

@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--output_dir', default=flaskconfig.get('VIDEO_OUTPUT_DIR'))
def main(dbname, dbuser, output_dir):

    output_dir = Path(output_dir)

    cpool = SimpleConnectionPool(1, 1, database=dbname, user=dbuser)
    
    schedule.every(5).minutes.do(run_ondeck, cpool, output_dir )

    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            print("sleeping for:", n)
            time.sleep(n)
        schedule.run_pending()

if __name__ == '__main__':
    main()
