
from model import Base, RiskVector, Test

import sqlalchemy as sa
from sqlalchemy.orm.session import Session

# from sqlalchemy.orm import session
from model.internetdata import InternetData

import json
import subprocess

import re
import codecs
import os

from datetime import datetime, timedelta, timezone

class ElogTimeGapsVector():

    # tests = relationship("Test")
    def __init__(self, session: Session, rv) -> None:
        self.session: Session = session
        self.config(rv)
    
    def config(self, rv):
        self.rv = rv
        config = json.loads(rv.configblob)
        print(self.rv)


    
    def execute(self, expected_timedelta: timedelta):
        datetime_to = datetime.now(tz=timezone.utc)
        datetime_from = datetime_to - expected_timedelta

        last_departure_res = self.session.execute(sa.text("""select max(datetime) last_departure from port_departures;"""))

        last_departure: datetime = last_departure_res.first()[0]
        
        result = Test(name="elog time gap vector at %s"%(datetime_to.strftime('%Y-%m-%d %H:%M:%SZ')), vector=self.rv)
        self.session.add(result)
        self.session.commit()
        # print(result)
        
        res = self.session.execute(sa.text("""
                                           select coalesce(max(score), 0) 
                                           from elog_time_gap_score 
                                           where ts_prev >= :recent_departure ;"""), {
                                               "recent_departure": last_departure
                                           })

        result.score = res.first()[0]
        
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
        session.execute(sa.text('delete from tests where vector_id = -1;'))
        session.execute(sa.text('delete from vectors where id = -1;'))
        rv = RiskVector()
        rv.id = -1
        rv.name = ElogTimeGapsVector.__name__
        rv.schedule_string = 'every 1 minutes'
        rv.configblob = '{}'
        rv.tests = []

        tmv = ElogTimeGapsVector(session, rv=rv)
        tmv.execute(timedelta(minutes=5))
        

    main()
