
from model import RiskVector, Test

from sqlalchemy.orm import session
from model.internetdata import InternetData

import json
import subprocess

import re
import codecs

from datetime import datetime, timedelta, timezone

class TegrastatsVector():
    namedpipe = ""

    # tests = relationship("Test")
    def __init__(self, session: session, rv) -> None:
        self.session = session
        self.config(rv)
    
    def config(self, rv):
        self.rv = rv
        config = json.loads(rv.configblob)
        self.namedpipe: list[str] = config['namedpipe']
        print(self.namedpipe)


    
    def execute(self, expected_timedelta: timedelta):
        datetime_to = datetime.now(tz=timezone.utc)
        datetime_from = datetime_to - expected_timedelta

        last = self.session.query(Test)\
            .where(Test.vector_id == self.rv.id, Test.datetime_to < datetime_to)\
            .order_by(Test.datetime_to.desc())\
            .limit(1).all()
        
        result = Test(name="tegrastats test at %s"%(datetime_to.strftime('%Y-%m-%d %H:%M:%SZ')), vector=self.rv)
        self.session.add(result)
        self.session.commit()
        # print(result)
        
        datas = []

        for statsline in tegrastats(self.namedpipe):
            print(statsline)
        
        result.score = 0.0
        
        self.session.commit()

        return result

def tegrastats(namedpipe):
    with open(namedpipe) as f:
        for l in f.readlines():
            yield(l)


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
    @click.option('--namedpipe')
    def main(dbname, dbuser, namedpipe):
    
        for i in tegrastats(namedpipe):
            print(i)

    main()

