
from model import Base, Track

if __name__ == '__main__':

    import os
    from flask.config import Config as FlaskConfig
    flaskconfig = FlaskConfig(root_path='')

    flaskconfig.from_object('config.defaults')
    if 'ENVIRONMENT' in os.environ:
        flaskconfig.from_envvar('ENVIRONMENT')

    import click

    @click.command()
    @click.option('--dbname', default=flaskconfig.get('DBNAME'))
    @click.option('--dbuser', default=flaskconfig.get('DBUSER'))
    def main(dbname, dbuser):

        import sqlalchemy as sa
        from sqlalchemy.orm import sessionmaker as SessionMaker

        sa_engine = sa.create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
        sessionmaker = SessionMaker(sa_engine)

        Base.metadata.create_all(sa_engine)
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

        
    
    main()
