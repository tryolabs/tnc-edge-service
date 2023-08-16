
import click
import json
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

def next_videos(session: Session, thalos_cam_name):
     workday_start_hour_at_utc_interval = '8 hours';
     workday_start_hour_at_utc_timestr = '08:00Z';
     num_vids_required = 4;
     results: Query[VideoFile] = session.query(VideoFile).from_statement(sa.text(
        """
        select video_files.* from video_files 
        join (
            select COALESCE(max(workday_counts.workday), '1970-01-01') most_recent_active_workday 
            from (
                select date(start_datetime AT TIME ZONE 'utc' - interval :timei ) as workday,
                    count(*) as count 
                from video_files 
                where decrypted_path is not null 
                group by workday
            ) workday_counts 
            where workday_counts.count > :numvids
        ) workdays 
        on video_files.start_datetime >= workdays.most_recent_active_workday + time with time zone :times 
        left join ondeckdata 
        on video_files.decrypted_path = ondeckdata.video_uri 
        where video_files.decrypted_path is not null 
        and ondeckdata.video_uri is null
        and video_files.cam_name = :cam_name
        order by video_files.decrypted_datetime asc;
        """)).params(
         {
             "timei": workday_start_hour_at_utc_interval,
             "times": workday_start_hour_at_utc_timestr,
             "numvids": num_vids_required,
             "cam_name": thalos_cam_name,
         })
     return list(results)


def run_ondeck(output_dir: Path, engine: Path, sessionmaker: SessionMaker, thalos_cam_name):
    
    video_files: list[VideoFile] = []

    with sessionmaker() as session:
        video_files = next_videos(session, thalos_cam_name)

    # print(video_files)
    while len(video_files) > 0:
        video_file: VideoFile = video_files.pop(0)
        # print(video_file)
        decrypted_path = Path(video_file.decrypted_path)
        last_dot_index: int = decrypted_path.name.index('.')
        if last_dot_index < 0:
            last_dot_index = None
        json_out_file: Path = output_dir / Path(decrypted_path.name[0:last_dot_index] + "_ondeck.json")
        # sudo /usr/bin/docker run --rm -v /videos:/videos --runtime=nvidia --network none gcr.io/edge-gcr/edge-service-image:latest --output /videos --input /videos/21-07-2023-09-55.avi
        cmd: str = "sudo /usr/bin/docker run --rm -v /videos:/videos --runtime=nvidia --network none \
                gcr.io/edge-gcr/edge-service-image:latest \
                --output %s --input %s"%(
            str(json_out_file.absolute()), 
            str(decrypted_path.absolute())
            )
        if engine:
            cmd += " --model %s"%( str(engine.absolute()), )
        p: CompletedProcess[str] = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if p.returncode == 0:

            with json_out_file.open() as f:
                o: dict = json.load(f)
                cnt = o.get('overallCount')
                runtime = o.get('overallRuntimeMs')
                frames = o.get('frames', default=[])
                trackedframes = filter(lambda frame: len(frame.get('trackingIds'))>0, frames)
                confidencesarrs = map(lambda frame: frame.get('confidence'), trackedframes)
                confidences = [c for confidencesarr in confidencesarrs for c in confidencesarr]
                meanconf = float(sum(confidences)) / float(len(confidences))

                with sessionmaker() as session:
                    session.execute(sa.text("insert into ondeckdata ( video_uri, cocoannotations_uri, \
                                            overallcount, overallruntimems, tracked_mean_confidence ) \
                                values ( :decrypted_path, :json_out_file , :cnt, :runt, :mean_c) ;"), {
                                    "decrypted_path": str(decrypted_path.absolute()),
                                    "json_out_file":str(json_out_file.absolute()),
                                    "cnt":cnt, 
                                    "runt":runtime, 
                                    "mean_c":meanconf,
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
            video_files = next_videos(session, thalos_cam_name)


@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--output_dir', default=flaskconfig.get('VIDEO_OUTPUT_DIR'))
@click.option('--engine', default=flaskconfig.get('ONDECK_MODEL_ENGINE'))
@click.option('--thalos_cam_name', default=flaskconfig.get('THALOS_CAM_NAME'))
@click.option('--print_queue', is_flag=True)
def main(dbname, dbuser, output_dir, engine, thalos_cam_name, print_queue):

    output_dir = Path(output_dir)

    if engine:
        engine = Path(engine)


    sa_engine = sa.create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    sessionmaker = SessionMaker(sa_engine)

    ModelBase.metadata.create_all(sa_engine)

    if print_queue:
        with sessionmaker() as session:
            video_files = next_videos(session, thalos_cam_name)
            for v in video_files:
                print(v.decrypted_path)
        return

    def runonce(output_dir, engine, sessionmaker, thalos_cam_name):
        run_ondeck(output_dir, engine, sessionmaker, thalos_cam_name)
        return schedule.CancelJob
    
    schedule.every(1).seconds.do(runonce, output_dir, engine, sessionmaker, thalos_cam_name)

    schedule.every(5).minutes.do(run_ondeck, output_dir, engine, sessionmaker, thalos_cam_name )

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

