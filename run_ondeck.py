
import click
import os
from pathlib import Path
import re
import schedule
import subprocess
from subprocess import CompletedProcess
import time

from model import Base as ModelBase, VideoFile, OndeckData
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker as SessionMaker, Query
from sqlalchemy.orm.session import Session

from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')

def next_videos(session: Session) -> list[VideoFile]:
     results: Query[VideoFile] = session.query(VideoFile
                        ).outerjoin(OndeckData, VideoFile.decrypted_path == OndeckData.video_uri
                        ).filter(VideoFile.decrypted_path != None
                        ).filter(OndeckData.video_uri == None
                        ).order_by(VideoFile.decrypted_datetime.asc())
     return list(results)


def run_ondeck(output_dir: Path, engine: Path, sessionmaker: SessionMaker):
    
    video_files: list[VideoFile] = []

    with sessionmaker() as session:
        video_files.extend(next_videos(session))

    # print(video_files)
    while len(video_files) > 0:
        video_file: VideoFile = video_files.pop(0)
        # print(video_file)
        decrypted_path = Path(video_file.decrypted_path)
        last_dot_index: int = decrypted_path.name.index('.')
        if last_dot_index < 0:
            last_dot_index = None
        json_out_file: Path = output_dir / Path(decrypted_path.name[0:last_dot_index] + "_ondeck.json")
        cmd: str = "docker run --rm -v /videos:/videos --runtime=nvidia --network none \
                gcr.io/edge-gcr/edge-service-image:latest \
                --output %s --input %s"%(
            str(json_out_file.absolute()), 
            str(decrypted_path.absolute())
            )
        if engine:
            cmd += " --model %s"%( str(engine.absolute()), )
        p: CompletedProcess[str] = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if p.returncode == 0:
            with sessionmaker() as session:
                session.execute(sa.text("insert into ondeckdata ( video_uri, cocoannotations_uri ) \
                            values ( :decrypted_path, :json_out_file ) ;"), {
                                "decrypted_path": str(decrypted_path.absolute()),
                                "json_out_file":str(json_out_file.absolute())
                        }
                )
                session.commit()
        else:
            # print("ondeck model failure. stdout, stderr:", p.stdout, p.stderr)
            with sessionmaker() as session:
                session.execute(sa.text("insert into ondeckdata ( video_uri, cocoannotations_uri ) \
                            values ( :decrypted_path, :error_str ) ;"), {
                                "decrypted_path": str(decrypted_path.absolute()),
                                "error_str": "ondeck model failure. stdout, stderr: " + p.stdout + p.stderr
                        }
                )
                session.commit()
        with sessionmaker() as session:
            video_files.extend(next_videos(session))


@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--output_dir', default=flaskconfig.get('VIDEO_OUTPUT_DIR'))
@click.option('--engine', default=None)
def main(dbname, dbuser, output_dir, engine):

    output_dir = Path(output_dir)

    if engine:
        engine = Path(engine)


    sa_engine = sa.create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    sessionmaker = SessionMaker(sa_engine)

    ModelBase.metadata.create_all(sa_engine)

    
    schedule.every(5).minutes.do(run_ondeck, output_dir, engine, sessionmaker )

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
