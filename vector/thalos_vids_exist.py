
from model import Base, RiskVector, Test

from sqlalchemy.orm.session import Session

from datetime import datetime, timedelta, timezone
import time

from pathlib import Path

import os
import json

MAGIC_20_MINUTES_IN_SECONDS = 20*60.0

from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')

thalosviddir = flaskconfig.get('THALOS_VIDEO_DIR')

class ThalosVideosExistVector():
    rv: RiskVector
    session: Session
    schedule_string: str = 'every 5 minutes'

    def __init__(self, session: Session, rv) -> None:
        self.session = session
        self.config(rv)
        
    
    def config(self, rv):
        self.rv = rv
        # config = json.loads(rv.configblob)
        print(self.rv)


    def execute(self, expected_timedelta: timedelta):

        if time.monotonic() < MAGIC_20_MINUTES_IN_SECONDS:
            # to recent from system boot time. don't run.
            return

        now = datetime.now().astimezone(timezone.utc);
        datetime_from = now - expected_timedelta

        nowfloor5min = now.replace(minute=(now.minute//5)*5, second=0, microsecond=0)
        nowfloorminus10min = nowfloor5min - timedelta(minutes=5)
        nowfloorminus15min = nowfloor5min - timedelta(minutes=10)
        
        nowstr = nowfloorminus15min.strftime('%d-%m-%Y-%H-%M')
        result = Test(name="thalos video files check, looking for %s "%(nowstr), vector=self.rv)


        
        self.session.add(result)
        self.session.commit()
        result.score = 1.0
        errors = []
        for cam in ['cam1', 'cam2']:
            try:
                mp4vid = Path(thalosviddir + '/' + cam + '/' + nowfloorminus15min.strftime('%d-%m-%Y') + '/' + nowfloorminus15min.strftime('%H') + '/' + nowstr + ".mp4.done")
                st = mp4vid.stat()
                # score based on size? I guess? larger than 1MiB is like 65% confident that the file is ok
                if st.st_size > 0:
                    result.score -= 0.25 * ( 1.0 - (1.0 / (1.0 +  st.st_size / 500000.0 )) )
            except Exception as e:
                print("error", type(e), e)
                errors.append(str(e))
            try:
                avivid = Path(thalosviddir + '/' + cam + '/' + nowfloorminus15min.strftime('%d-%m-%Y') + '/' + nowfloorminus15min.strftime('%H') + '/' + nowstr + ".avi.done")
                st = avivid.stat()
                
                # score based on size? I guess? larger than 1MiB is like 65% confident that the file is ok
                if st.st_size > 0:
                    result.score -= 0.25 * ( 1.0 - (1.0 / (1.0 +  st.st_size / 500000.0 )) )
            except Exception as e:
                print("error", type(e), e)
                errors.append(str(e))
        if len(errors)> 0:
            result.detail = "\n".join(errors)
        self.session.commit()

        return result


# test by running directly with `python3 -m vector.fname`
if __name__ == '__main__':

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
        session = sessionmaker()
        # results = list(session.query(RiskVector).filter(RiskVector.name == ThalosVideosExistVector.__name__))
        rv = RiskVector()
        rv.id = -1
        rv.name = ThalosVideosExistVector.__name__
        rv.schedule_string = 'every 1 minutes'
        rv.configblob = '{}'
        rv.tests = []

        tmv = ThalosVideosExistVector(session, rv=rv)
        tmv.execute(timedelta(minutes=5))
        

    main()
