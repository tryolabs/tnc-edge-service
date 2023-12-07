
from model import Base, Track, OndeckData

import os
from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')


import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker as SessionMaker, Session

import click

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
def main(ctx, dbname, dbuser):

    sa_engine = sa.create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    sessionmaker = SessionMaker(sa_engine)

    Base.metadata.create_all(sa_engine)

    ctx.ensure_object(dict)
    ctx.obj['sessionmaker'] = sessionmaker

    if ctx.invoked_subcommand is None:
        # click.echo('I was invoked without subcommand')

        with sessionmaker() as session:
            active_tracks = {}
            done_tracks = []
            fname = '/Users/ericfultz/Documents/pops/TNC/tnc-edge-service/20231205T212500Z_cam1_ondeck.json'
            import json
            with open(fname) as f:

                j = json.load(f)
                for frame in j['frames']:
                    if 'allActiveTrackingIds' not in frame:
                        continue
                    for activeTrackingId_str in frame['allActiveTrackingIds']:
                        activeTrackingId = int(activeTrackingId_str)
                        if activeTrackingId not in active_tracks.keys():
                            active_tracks[activeTrackingId] = Track()
                            active_tracks[activeTrackingId].cocoannotations_uri = fname
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
                            track.last_framenum = frame['frameNum']
                            done_tracks.append(track)
                            active_tracks.pop(track_id)
                    
                
            session.add_all(done_tracks)          


            session.commit()

        
@main.command()
@click.pass_context
def archive(ctx):
    import run_ondeck
    from pathlib import Path

    sessionmaker = ctx.obj['sessionmaker']
    session: Session = sessionmaker()
    with session:
        res = session.execute(sa.text("select ondeckdata.video_uri, ondeckdata.cocoannotations_uri from ondeckdata \
                                      left join tracks on ondeckdata.cocoannotations_uri = tracks.cocoannotations_uri \
                                      where tracks.id is null and ondeckdata.cocoannotations_uri like '/videos/%ondeck.json';"))
        for (video_uri, json_uri) in res:
            run_ondeck.parse_json(session, Path(video_uri), Path(json_uri), only_tracks=True)

if __name__ == '__main__':
    main()
