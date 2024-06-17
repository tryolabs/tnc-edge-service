
from model import Base, RiskVector, Test

from sqlalchemy.orm.session import Session

from datetime import datetime, timedelta, timezone

from pathlib import Path

import os
import json



class ThalosMountVector():
    rv: RiskVector
    session: Session
    schedule_string: str = 'every 10 minutes'

    def __init__(self, session: Session, rv) -> None:
        self.session = session
        self.config(rv)
        
    
    def config(self, rv):
        self.rv = rv
        # config = json.loads(rv.configblob)
        print(self.rv)


    def execute(self, expected_timedelta: timedelta):

        now = datetime.now();
        datetime_from = now - expected_timedelta

        nowstr = now.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
        result = Test(name="thalos mounted network dir, run at %s "%(nowstr), vector=self.rv)

        
        self.session.add(result)
        self.session.commit()
        result.score = 1.0
        try:
            thalosdir = Path('/thalos/')
            for boatpath in thalosdir.iterdir():
                for camdirs in (boatpath / "videos").iterdir():
                    datedirs = [ datedir.name for datedir in camdirs.iterdir() ]
                    if len(datedirs) > 0:
                        result.score -= 0.125
                        if now.astimezone(timezone.utc).strftime('%d-%m-%Y') in datedirs:
                            result.score -= 0.125
            if result.score < 1.0:
                result.score -= 0.5
        except Exception as e:
            print("error", type(e), e)
            result.detail = str(e)
        finally:       
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
        results = list(session.query(RiskVector).filter(RiskVector.name == ThalosMountVector.__name__))
        tmv = ThalosMountVector(session, rv=results[0])
        tmv.execute(None, None)
        

    main()
