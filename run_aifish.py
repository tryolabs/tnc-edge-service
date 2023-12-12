
from datetime import datetime, timezone
import click
import json
import os
from pathlib import Path
import re
import requests
from requests import Response
import schedule
import subprocess
from subprocess import CompletedProcess
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

MAGIC_VALUE_5_MiB = 5 * 1024 * 1024


def parse_json(session: Session, decrypted_path: Path, json_out_file: Path, only_tracks=False):
    with json_out_file.open() as f:
        o: dict = json.load(f)
    
        cnt = o.get('overallCount')
        catches = o.get('overallCatches')
        discards = o.get('overallDiscards')
        runtime = o.get('overallRuntimeSeconds')
        frames = o.get('frames', [])


        detectionconfidences = []
        # trackedconfidences = []

        active_tracks = {}
        done_tracks: list[Track] = []
                        
                        

        for frame in frames:
            detectionconfidences.extend(frame.get('confidence'))
            
            # idx = 0
            # for trackingId in frame.get('trackingIds'):
            #     if trackingId in frame.get('allActiveTrackingIds'):
            #         trackedconfidences.append(frame.get('confidence')[idx])
            #     idx += 1
            
            if 'allActiveTrackingIds' not in frame:
                continue
            for activeTrackingId_str in frame['allActiveTrackingIds']:
                activeTrackingId = int(activeTrackingId_str)
                if activeTrackingId not in active_tracks.keys():
                    active_tracks[activeTrackingId] = Track()
                    active_tracks[activeTrackingId].video_uri = str(decrypted_path.absolute())
                    active_tracks[activeTrackingId].cocoannotations_uri = str(json_out_file.absolute())
                    active_tracks[activeTrackingId].track_id = activeTrackingId
                    active_tracks[activeTrackingId].first_framenum = frame['frameNum']
                    active_tracks[activeTrackingId].confidences = []
                t = active_tracks[activeTrackingId]
                try: 
                    idx = frame['trackingIds'].index(activeTrackingId_str)
                    t.confidences.append(frame['confidence'][idx])
                except:
                    t.confidences.append(0.0)
            for track_id in list(active_tracks.keys()):
                track = active_tracks[track_id]
                if str(track_id) not in frame['allActiveTrackingIds']:
                    # the confidences will probably have a long trail of 0s at the end, which are not useful
                    # cut them out
                    track.confidences.reverse()
                    last_nonzero_index = next((i for (i,x) in enumerate(track.confidences) if x), None)
                    track.confidences.reverse()
                    if last_nonzero_index:
                        track.confidences = track.confidences[:-last_nonzero_index]

                    track.last_framenum = frame['frameNum']
                    done_tracks.append(track)
                    active_tracks.pop(track_id)

                    
        session.add_all(done_tracks)


        session.commit()

        if only_tracks:
            return
        
        if len(detectionconfidences) > 0:
            meandetectionconfidence = float(sum(detectionconfidences)) / float(len(detectionconfidences))
        else:
            meandetectionconfidence = 0


        if len(done_tracks) > 0:
            tracks_avg_conf = list(map(lambda t: float(sum(t.confidences)) / float(len(t.confidences)) if len(t.confidences) else 0.0, done_tracks))
            meantrackedconfidence = float(sum(tracks_avg_conf)) / float(len(tracks_avg_conf)) if len(tracks_avg_conf) else 0.0
        else:
            meantrackedconfidence = 0
                        

        # with sessionmaker() as session:
        session.execute(sa.text("""insert into ondeckdata ( video_uri, cocoannotations_uri, 
                                        overallcount, overallcatches, overalldiscards, overallruntimems, detection_confidence, tracked_confidence ) 
                            values ( :decrypted_path, :json_out_file , :cnt, :catches, :discards, :runt, :mean_c, :mean_t) 
                            on conflict (video_uri) do update set 
                            cocoannotations_uri = :json_out_file,
                            overallcount = :cnt,
                            overallruntimems = :runt,
                            tracked_confidence = :mean_t,
                            overallcatches = :catches,
                            overalldiscards = :discards,
                            detection_confidence = :mean_c
                            ;"""), {
                                "decrypted_path": str(decrypted_path.absolute()),
                                "json_out_file":str(json_out_file.absolute()),
                                "cnt":cnt, 
                                "catches":catches, 
                                "discards":discards,
                                "runt":runtime, 
                                "mean_c":meandetectionconfidence,
                                "mean_t":meantrackedconfidence,
                        }
                )
        session.commit()

def v2_next_videos(session: Session, thalos_cam_name):
     results: Query[VideoFile] = session.query(VideoFile).from_statement(sa.text(
        """
        select video_files.* from video_files 
        left join ondeckdata 
        on video_files.decrypted_path = ondeckdata.video_uri 
        where video_files.decrypted_path is not null 
        and video_files.start_datetime is not null
        and ondeckdata.video_uri is null
        and video_files.cam_name = :cam_name
        order by video_files.start_datetime asc;
        """)).params(
         {
             "cam_name": thalos_cam_name,
         })
     return list(results)

def enqueue(output_dir: Path, sessionmaker: SessionMaker, thalos_cam_name: str):
    
    video_files: list[VideoFile] = []

    with sessionmaker() as session:
        video_files = next_videos(session, thalos_cam_name)

        # print(video_files)
        while len(video_files) > 0:
            video_file: VideoFile = video_files.pop(0)
            # print(video_file)
            decrypted_path = Path(video_file.decrypted_path)

            rname = decrypted_path.name[::-1]
            last_dot_index: int = rname.find('.')
            if last_dot_index < 0:
                json_out_file: Path = output_dir / Path(decrypted_path.name + ".json")
            else:
                json_out_file: Path = output_dir / Path(decrypted_path.name[0:-last_dot_index-1] + ".json")

            aifish_processing_path = decrypted_path.parent / 'processing' / decrypted_path.name

            decrypted_path.rename(aifish_processing_path)

            with sessionmaker() as session:
                session.execute(sa.text("""insert into aifishdata ( video_uri, processing_uri, output_uri, status )
                            values ( :video_uri, :processing_uri, :output_uri, :status )
                            on conflict (video_uri) DO UPDATE SET status = :status ;"""), {
                                "video_uri": str(decrypted_path.absolute()),
                                "processing_uri": str(aifish_processing_path.absolute()),
                                "ondeck_output": str(json_out_file.absolute()),
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
            
            click.echo("found {} queued row".format(str(pending_aifishdata)))

            if pending_aifishdata.output_uri in found_aifish_files:

                video = Path(pending_aifishdata.video_uri)
                processing = Path(pending_aifishdata.processing_uri)
                output = Path(pending_aifishdata.output_uri)

                ptime = processing.stat().st_mtime
                otime = output.stat().st_mtime

                pending_aifishdata.runtimems = (otime - ptime) * 1000.0
                pending_aifishdata.status = "parsing"
                session.commit()
                
                processing.rename(Path(pending_aifishdata.video_uri))
        
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

@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--output_dir', default=flaskconfig.get('VIDEO_OUTPUT_DIR'))
@click.option('--engine', default=flaskconfig.get('ONDECK_MODEL_ENGINE'))
@click.option('--thalos_cam_name', default=flaskconfig.get('THALOS_CAM_NAME'))
@click.option('--print_queue', is_flag=True)
@click.option('--parsetesta')
@click.option('--parsetestb')
@click.option('--force_v2', is_flag=True)
def main(dbname, dbuser, output_dir, engine, thalos_cam_name, print_queue, parsetesta, parsetestb, force_v2: bool):

    output_dir = Path(output_dir)

    if engine:
        engine = Path(engine)


    sa_engine = sa.create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    sessionmaker = SessionMaker(sa_engine)

    ModelBase.metadata.create_all(sa_engine)

    if parsetesta and parsetestb:
        parse_json(sessionmaker, Path(parsetesta), Path(parsetestb))
        return

    if print_queue:
        with sessionmaker() as session:
            video_files = next_videos(session, thalos_cam_name)
            for v in video_files:
                click.echo(v.decrypted_path)
        return

    use_v2 = False
    try:
        r: Response = requests.get('http://127.0.0.1:5000/queueSummary')
        use_v2 = r.status_code == 200
        click.echo("resp: {} body: {}".format(repr(r), repr(r.json())))
    except requests.exceptions.RequestException as e:
        click.echo("ondeck model request exception: {}".format(e))

        
    def runonce_enqueue(output_dir, sessionmaker, thalos_cam_name):
        enqueue(output_dir, sessionmaker, thalos_cam_name)
        return schedule.CancelJob
    
    schedule.every(1).seconds.do(runonce_enqueue, output_dir, sessionmaker, thalos_cam_name)

    schedule.every(5).minutes.do(enqueue, output_dir, sessionmaker, thalos_cam_name )

    def runonce_errors(sessionmaker):
        errors(sessionmaker)
        return schedule.CancelJob
    
    schedule.every(1).seconds.do(runonce_errors, sessionmaker) 

    schedule.every(1).minutes.do(errors, sessionmaker)

    def runonce_parse(output_dir, sessionmaker):
        parse(output_dir, sessionmaker)
        return schedule.CancelJob
    
    schedule.every(1).seconds.do(runonce_parse, output_dir, sessionmaker)

    schedule.every(1).minutes.do(parse, output_dir, sessionmaker )
    

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

