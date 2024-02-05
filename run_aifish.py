
from datetime import datetime, timezone, timedelta
from dateutil import parser
import click
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import requests
from requests import Response
import schedule
import shutil
import subprocess
from subprocess import CompletedProcess
import sys
import time

from model import Base as ModelBase, VideoFile, AifishData, Track
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker as SessionMaker, Query
from sqlalchemy.orm.session import Session

from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')


# select video_files.* from video_files 
# join (
#     select COALESCE(max(workday_counts.workday), '1970-01-01') most_recent_active_workday 
#     from (
#         select date(start_datetime AT TIME ZONE 'utc' - interval '8 hours' ) as workday,
#             count(*) as count 
#         from video_files 
#         where decrypted_path is not null 
#         group by workday
#     ) workday_counts 
#     where workday_counts.count > 4
# ) workdays 
# on video_files.start_datetime >= workdays.most_recent_active_workday + time with time zone '08:00Z'
# left join aifishdata 
# on video_files.decrypted_path = aifishdata.video_uri 
# where video_files.decrypted_path is not null 
# and aifishdata.video_uri is null
# and video_files.cam_name = 'cam1'
# order by video_files.decrypted_datetime asc;

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
        left join aifishdata 
        on video_files.decrypted_path = aifishdata.video_uri 
        where video_files.decrypted_path is not null 
        and aifishdata.video_uri is null
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

def v2_next_videos(session: Session, thalos_cam_name):
     results: Query[VideoFile] = session.query(VideoFile).from_statement(sa.text(
        """
        select video_files.* from video_files 
        left join aifishdata 
        on video_files.decrypted_path = aifishdata.video_uri 
        where video_files.decrypted_path is not null 
        and video_files.start_datetime is not null
        and aifishdata.video_uri is null
        and video_files.cam_name = :cam_name
        order by video_files.start_datetime asc;
        """)).params(
         {
             "cam_name": thalos_cam_name,
         })
     return list(results)


MAGIC_VALUE_5_MiB = 5 * 1024 * 1024


def parse_json(session: Session, decrypted_path: Path, json_out_file: Path, only_tracks=False):
    with json_out_file.open() as f:
        detections = [json.loads(line) for line in f]

        if len(detections) == 0:
            # error handling here
            pass
        
        fish_detections = list(filter(lambda d: d.get('class_name') == 'fish', detections))

        if len(fish_detections) == 0:
            # error handling here
            if only_tracks:
                return
            session.execute(sa.text("""insert into aifishdata ( video_uri, output_uri, 
                                        count, detection_confidence ) 
                            values ( :decrypted_path, :json_out_file , :cnt, :mean_c) 
                            on conflict (video_uri) do update set 
                            output_uri = :json_out_file,
                            count = :cnt,
                            detection_confidence = :mean_c
                            ;"""), {
                                "decrypted_path": str(decrypted_path.absolute()),
                                "json_out_file":str(json_out_file.absolute()),
                                "cnt": 0, 
                                "mean_c": 0,
                        }
                )
            session.commit()
            return

        last_frame = max(map(lambda d: d.get('frame'), detections))
        frames = []

        detectionconfidences = list(filter(lambda x: x is not None, map(lambda d: d.get('object_confidence'), fish_detections)))
        # = max(map(lambda detection: detection.get('object_confidence'), detections))
        # trackedconfidences = []

        tracks = defaultdict(list)
        for d in fish_detections:
            tracks[d.get('track')].append(d)
        
        cnt = len(tracks.keys())

        done_tracks = []

        for track_id, detections in tracks.items():
            frame_nums = list(map(lambda d: d.get('frame'), detections))
            min_frame = min(frame_nums)
            max_frame = max(frame_nums)

            t = Track()
            t.video_uri = str(decrypted_path.absolute())
            t.cocoannotations_uri = str(json_out_file.absolute())
            t.track_id = track_id
            t.first_framenum = min_frame
            t.last_framenum = max_frame
            t.confidences = [0 for i in range(1 + max_frame - min_frame)]
            for d in detections:
                t.confidences[d.get('frame') - min_frame] = d.get('object_confidence') or 0
            done_tracks.append(t)
        session.add_all(done_tracks)
        session.commit()

        if only_tracks:
            return
        
        if len(detectionconfidences) > 0:
            meandetectionconfidence = float(sum(detectionconfidences)) / float(len(detectionconfidences))
        else:
            meandetectionconfidence = 0


        # with sessionmaker() as session:
        session.execute(sa.text("""insert into aifishdata ( video_uri, output_uri, 
                                        count, detection_confidence ) 
                            values ( :decrypted_path, :json_out_file , :cnt, :mean_c) 
                            on conflict (video_uri) do update set 
                            output_uri = :json_out_file,
                            count = :cnt,
                            detection_confidence = :mean_c
                            ;"""), {
                                "decrypted_path": str(decrypted_path.absolute()),
                                "json_out_file":str(json_out_file.absolute()),
                                "cnt":cnt, 
                                "mean_c":meandetectionconfidence,
                        }
                )
        session.commit()

VIDEO_TOO_SMALL = 1024*1024

def enqueue(output_dir: Path, sessionmaker: SessionMaker, thalos_cam_name: str):
    
    video_files: list[VideoFile] = []

    with sessionmaker() as session:
        video_files = next_videos(session, thalos_cam_name)

        # print(video_files)
        while len(video_files) > 0:
            video_file: VideoFile = video_files.pop(0)
            # print(video_file)
            decrypted_path = Path(video_file.decrypted_path)

            # use_reencoded = False
            v_source_path = str(decrypted_path.absolute())
            v_source_name = decrypted_path.name
            if not decrypted_path.exists() or not decrypted_path.is_file() or decrypted_path.stat().st_size < VIDEO_TOO_SMALL:
                click.echo(f"original video file {decrypted_path.name} failed basic checks. Using reencoded")
                # use_reencoded = True
                if video_file.reencoded_path is None:
                    click.echo(f"video not reencoded, skipping video")
                    continue
                reencoded_path = Path(video_file.reencoded_path)
                v_source_path = str(reencoded_path.absolute())
                v_source_name = reencoded_path.name
                if not reencoded_path.exists() or not reencoded_path.is_file() or reencoded_path.stat().st_size < VIDEO_TOO_SMALL:
                    click.echo(f"reencoded_video {reencoded_path.name} fails basic checks. skipping video")
                    continue

            rname = v_source_name[::-1]
            last_dot_index: int = rname.find('.')
            if last_dot_index < 0:
                json_out_file: Path = output_dir / Path(v_source_name + ".json")
            else:
                json_out_file: Path = output_dir / Path(v_source_name[0:-last_dot_index-1] + ".json")

            aifish_processing_path = decrypted_path.parent / 'processing' / v_source_name

            # decrypted_path.rename(aifish_processing_path)

            # aifish_processing_path.touch()
            # with aifish_processing_path.open('a') as _:
            #     pass

            shutil.copy(v_source_path, aifish_processing_path)

            with sessionmaker() as session:
                session.execute(sa.text("""insert into aifishdata ( video_uri, processing_uri, output_uri, status )
                            values ( :video_uri, :processing_uri, :output_uri, :status )
                            on conflict (video_uri) DO UPDATE SET status = :status ;"""), {
                                "video_uri": str(decrypted_path.absolute()),
                                "processing_uri": str(aifish_processing_path.absolute()),
                                "output_uri": str(json_out_file.absolute()),
                                "status": "queued"
                        }
                )
                session.commit()

MAGIC_VALUE_1_MINUTE = 60

def parse(output_dir: Path, sessionmaker: SessionMaker):
    # only pick files that end with .json
    a = filter(lambda x: x.is_file() and x.name.endswith('.json'), output_dir.iterdir())

    epoch_now = int(time.time())
    # only pick files that haven't been modified in the last minute
    b = filter(lambda x: x.stat().st_mtime + MAGIC_VALUE_1_MINUTE < epoch_now, a)

    # get the filenames
    c = map(lambda x: str(x.absolute()) , b)

    found_aifish_files = list(c)

    click.echo("found {} .json files".format(str(len(found_aifish_files))))

    with sessionmaker() as session:
        results: Query[AifishData] = session.query(AifishData).where( AifishData.status == 'queued' )
        for pending_aifishdata in results:
            
            # click.echo("found {} queued row".format(str(pending_aifishdata)))

            if pending_aifishdata.output_uri in found_aifish_files:

                video = Path(pending_aifishdata.video_uri)
                processing = Path(pending_aifishdata.processing_uri)
                output = Path(pending_aifishdata.output_uri)

                otime = output.stat().st_mtime
                if processing.exists():
                    ptime = processing.stat().st_mtime
                    pending_aifishdata.runtimems = (otime - ptime) * 1000.0

                pending_aifishdata.status = "parsing"
                session.commit()

                if processing.exists():
                    processing.unlink()
        
                parse_json(session, video, output)

                pending_aifishdata.status = "done"
                session.commit()

                


def errors(sessionmaker: SessionMaker):
    try:
        r: Response = requests.get('http://127.0.0.1:5000/errors')

        click.echo("errors resp: {} body: {}".format(repr(r), repr(r.json())))

        for error in r.json():
            input_path = error.get('input_path')
            error_message = error.get('error_message')

            if error_message.startswith('Task performance mode set to SKIP'):
                with sessionmaker() as session:
                    session.execute(sa.text("""insert into ondeckdata ( video_uri, status ) 
                                values ( :decrypted_path, :skiphalfstatus ) 
                                on conflict (video_uri) do update set 
                                status = :skiphalfstatus
                                ;"""), {
                                    "decrypted_path": input_path,
                                    "skiphalfstatus": "runningskiphalf"
                            }
                    )
                    session.commit()
                continue

            with sessionmaker() as session:
                session.execute(sa.text("""insert into ondeckdata ( video_uri, cocoannotations_uri ) 
                            values ( :decrypted_path, :error_str ) 
                            on conflict (video_uri) do update set 
                            status = 'errored', cocoannotations_uri = :error_str
                            ;"""), {
                                "decrypted_path": input_path,
                                "error_str": "ondeck model failure. stdout, stderr: " + error_message
                        }
                )
                session.commit()

    except requests.exceptions.RequestException as e:
        click.echo("ondeck model errors request exception: {}".format(e))
        return

LOST_TIME_BUFFER = timedelta(minutes=30)

def lost_inprogress(sessionmaker: SessionMaker, aifish_processing_dir: Path):
    last_start_time_s = subprocess.run('journalctl -o short-iso -u aifish_model.service | grep systemd | grep Started | tail -n 1 | sed "s/edge.*//"', shell=True, text=True, capture_output=True)
    last_start_time_dt = parser.parse(last_start_time_s.stdout)


    check_these = list(filter(
        lambda f: f.is_file() 
            and (f.name.endswith('.avi') 
                or f.name.endswith('.mkv'))
            and datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc) + LOST_TIME_BUFFER < last_start_time_dt,
        aifish_processing_dir.iterdir()
    ))
    if len(check_these) > 0:
        abs_names = list(map(lambda f: str(f.absolute()), check_these))
        with sessionmaker() as session:
            rows: Query = session.query(AifishData) \
                .filter(AifishData.processing_uri.in_(abs_names)) \
                .filter(AifishData.status == 'queued')
            for lost_file in rows.all():
                click.echo(f'found lost file in progress - deleting: {lost_file.processing_uri}')
                Path(lost_file.processing_uri).unlink()
                lost_file.status = 'errored'
                session.commit()    


def ensure_is_dir(p: Path):
    if p is None:
        return
    a = str(p.absolute())
    if not p.exists() or not p.is_dir():
        click.echo(f"folder {a} does not exist. Creating")
        try:
            p.mkdir()
        except:
            pass
        if not p.exists() or not p.is_dir():
            click.echo(f"Could not create folder {a}. Exiting")
            sys.exit(1)

@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--output_dir', default=flaskconfig.get('VIDEO_OUTPUT_DIR'))
@click.option('--engine', default=flaskconfig.get('ONDECK_MODEL_ENGINE'))
@click.option('--thalos_cam_name', default=flaskconfig.get('THALOS_CAM_NAME'))
@click.option('--print_queue', is_flag=True)
@click.option('--parsetesta')
@click.option('--parsetestb')
@click.option('--testlostinprogress', is_flag=True)
def main(dbname, dbuser, output_dir, engine, thalos_cam_name, print_queue, parsetesta, parsetestb, testlostinprogress):

    video_output_dir = Path(output_dir)
    aifish_processing_dir = video_output_dir / 'processing'
    aifish_output_dir = video_output_dir / 'output'

    ensure_is_dir(aifish_processing_dir)
    ensure_is_dir(aifish_output_dir)

    if engine:
        engine = Path(engine)


    sa_engine = sa.create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    sessionmaker = SessionMaker(sa_engine)

    ModelBase.metadata.create_all(sa_engine)

    if parsetesta and parsetestb:
        with sessionmaker() as session:
            parse_json(session, Path(parsetesta), Path(parsetestb))
        return

    if print_queue:
        with sessionmaker() as session:
            video_files = next_videos(session, thalos_cam_name)
            for v in video_files:
                click.echo(v.decrypted_path)
        return

    if testlostinprogress:
        lost_inprogress(sessionmaker, aifish_processing_dir)
        return

        
    def runonce_enqueue(aifish_output_dir, sessionmaker, thalos_cam_name):
        enqueue(aifish_output_dir, sessionmaker, thalos_cam_name)
        return schedule.CancelJob
    
    schedule.every(1).seconds.do(runonce_enqueue, aifish_output_dir, sessionmaker, thalos_cam_name)

    schedule.every(5).minutes.do(enqueue, aifish_output_dir, sessionmaker, thalos_cam_name )

    def runonce_errors(sessionmaker):
        errors(sessionmaker)
        return schedule.CancelJob
    
    schedule.every(1).seconds.do(runonce_errors, sessionmaker) 

    schedule.every(1).minutes.do(errors, sessionmaker)

    def runonce_parse(aifish_output_dir, sessionmaker):
        parse(aifish_output_dir, sessionmaker)
        return schedule.CancelJob
    
    schedule.every(1).seconds.do(runonce_parse, aifish_output_dir, sessionmaker)

    schedule.every(1).minutes.do(parse, aifish_output_dir, sessionmaker )
    

    # def runonce_lost_inprogress(sessionmaker, aifish_processing_dir):
    #     lost_inprogress(sessionmaker, aifish_processing_dir)
    #     return schedule.CancelJob
    # schedule.every(1).seconds.do(runonce_lost_inprogress, sessionmaker, aifish_processing_dir)
    # schedule.every(5).minutes.do(lost_inprogress, sessionmaker, aifish_processing_dir )



    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            click.echo("sleeping for: {}".format(n))
            time.sleep(n)
        schedule.run_pending()

if __name__ == '__main__':
    main()
