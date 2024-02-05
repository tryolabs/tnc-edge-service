
from model import RiskVector, Test

import sqlalchemy as sa
from sqlalchemy.orm import Session
from model import Base, OndeckData, VideoFile, DeckhandEventView

import json
import subprocess

import re
import codecs
import os
import math

from datetime import datetime, timezone, timedelta

import pandas as pa
import numpy as np

from pathlib import Path

class CatchCountA():

    # tests = relationship("Test")
    def __init__(self, session: Session, rv) -> None:
        self.session: Session = session
        self.config(rv)
    
    def config(self, rv):
        self.rv = rv
        config = json.loads(rv.configblob)

        self.window_minutes = config['window_minutes']
        self.ai_table = config['ai_table']

        self.confidence_filter = None
        if 'confidence_filter' in config.keys():
            self.confidence_filter = config['confidence_filter']

        self.ok_p_coeff = 0.2
        if 'ok_p_coeff' in config.keys():
            self.ok_p_coeff = config['ok_p_coeff']
        
        print(self.rv)
        print(self.ai_table)


    
    def execute(self, expected_timedelta):
        datetime_to = datetime.now(tz=timezone.utc)
        datetime_from = datetime_to - timedelta(minutes = self.window_minutes)

        
        result = Test(name=f"catch count A test from {datetime_from:%Y-%m-%d %H:%M} to {datetime_to:%Y-%m-%d %H:%M}", vector=self.rv)
        self.session.add(result)
        self.session.commit()
        # print(result)
        
        datas = []

        recent_elogs: list[DeckhandEventView] = self.session.query(DeckhandEventView).where(
                DeckhandEventView.datetime > datetime_to - 2*timedelta(minutes = self.window_minutes)).all()

        if self.ai_table == 'ondeckdata':
            ondeck_datas = self.session.query(OndeckData) \
                .join(OndeckData.video_file) \
                .options(sa.orm.joinedload(OndeckData.video_file)) \
                .where(
                    VideoFile.start_datetime < datetime_to,
                    VideoFile.start_datetime >= datetime_from) \
                .order_by(OndeckData.datetime).all()
            
            ondeck_datas: list[OndeckData] = list(ondeck_datas)

            expected_videos = self.window_minutes / 5.0
            errored = len(list(filter(lambda x: x.status != 'done',  ondeck_datas)))

            # print(f"ondeck errored: {errored}")

            if self.confidence_filter:
                # redo list of tracks, based on a higher confidence value
                try:
                    files = list(map(lambda x: Path(x.cocoannotations_uri), ondeck_datas))
                    for file in files:
                        s = file.stat()
                        if s.st_size <= 0:
                            print("empty file", file)
                            
                except Exception as e:
                    print("exception", e)
            
            fish_counts = []
            is_fishings = []
            dts = []

            for row in ondeck_datas:
                if int != type(row.overallcatches):
                    continue
                fish_counts.append(row.overallcatches)
                dts.append(row.video_file.start_datetime)
                is_fishing = any(map(lambda elog: \
                                    elog.systemstarthauldatetime < row.video_file.start_datetime and \
                                    row.video_file.start_datetime < elog.systemendhauldatetime, recent_elogs))
                is_fishings.append(int(is_fishing))

            a = pa.DataFrame({
                'datetime': dts,
                "fish_counts": fish_counts,
                "is_fishings": is_fishings,
            })
            
            # from matplotlib import pyplot
            # pyplot.axis()
            # pyplot.plot(a['datetime'],a['fish_counts'])
            # pyplot.plot(a['datetime'],a['is_fishings'])
            # pyplot.show()
            
            if not np.any(np.diff(is_fishings)):
                # this means there is no overlap with the elogs, so the is_fishings data is a flat line
                # running a p_coeff when one input is a flat line is meaningless
                # so this test can't continue
                result.detail = "elog reports a flat is_fishing variable over time. p_coeff can't work"
                self.session.commit()
                return

            
            if not np.any(np.diff(fish_counts)):
                result.detail = "ondeck reports a flat fish count over time. p_coeff can't work"
                self.session.commit()
                return

            p_coeffs = np.corrcoef(np.array(fish_counts), np.array(is_fishings))

            print(p_coeffs)
            p_coeff = p_coeffs[0][1]
        
            
            result.score = math.sqrt(self.ok_p_coeff - p_coeff) if p_coeff <= self.ok_p_coeff else 0
            
            self.session.commit()
        elif self.ai_table == 'tracks':
            tracks_rows = self.session.execute(sa.text('select t.*, v.start_datetime from tracks t \
                                                       join video_files v on t.video_uri = v.decrypted_path \
                                                       where v.start_datetime > :datetime_from \
                                                       and v.start_datetime <= :datetime_to \
                                                       order by t.datetime asc;'), {
                                                       'datetime_from': datetime_from,
                                                       'datetime_to': datetime_to,
                                                       })
            tracks: list[Track] = list(tracks_rows)

            expected_videos = self.window_minutes / 5.0
            # errored = len(list(filter(lambda x: x.status != 'done',  tracks)))

            # print(f"ondeck errored: {errored}")

            # print(list(map(lambda t: fmean(t.confidences), tracks)))

            if self.confidence_filter:
                # redo list of tracks, based on a higher confidence value
                tracks = list(filter(lambda t: fmean(t.confidences) > 0.6, tracks))

            fish_counts = {}

            for row in tracks:
                # if int != type(row.overallcatches):
                #     continue
                if row.start_datetime not in fish_counts.keys():
                    fish_counts[row.start_datetime] = 0
                fish_counts[row.start_datetime] += 1

            fishCountS =pa.Series(fish_counts)
            fishCountS.sort_index(inplace=True)

            is_fishings = {}

            for start_datetime in fish_counts.keys():
                is_fishing = any(map(lambda elog: \
                                    elog.systemstarthauldatetime < start_datetime and \
                                    start_datetime < elog.systemendhauldatetime, recent_elogs))
                is_fishings[start_datetime] = int(is_fishing)

            isFishingS = pa.Series(is_fishings)
            isFishingS.sort_index(inplace=True)

            a = pa.DataFrame({
                "fish_counts": fishCountS,
                "is_fishings": isFishingS
            })
            # print(a)

            # from matplotlib import pyplot
            # pyplot.axis()
            # pyplot.plot(isFishingS)
            # pyplot.plot(fishCountS)
            # pyplot.show()
            
            if not np.any(np.diff(isFishingS.values)):
                # this means there is no overlap with the elogs, so the is_fishings data is a flat line
                # running a p_coeff when one input is a flat line is meaningless
                # so this test can't continue
                result.detail = "elog reports a flat is_fishing variable over time. p_coeff can't work"
                self.session.commit()
                return

            
            if not np.any(np.diff(fishCountS.values)):
                result.detail = "ondeck reports a flat fish count over time. p_coeff can't work"
                self.session.commit()
                return

            p_coeffs = np.corrcoef(fishCountS.values, isFishingS.values)

            print("p_coeffs:", p_coeffs)
            p_coeff = p_coeffs[0][1]
        
            
            result.score = math.sqrt(self.ok_p_coeff - p_coeff) if p_coeff <= self.ok_p_coeff else 0
            
            self.session.commit()

        return


   

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
        session.execute('delete from tests where vector_id = -1;')
        session.execute('delete from vectors where id = -1;')
        rv = RiskVector()
        rv.id = -1
        rv.name = CatchCountA.__name__
        rv.schedule_string = 'every 1 minutes'
        rv.configblob = '{"window_minutes": 60000, "ai_table":"ondeckdata"}'
        rv.tests = []

        tmv = CatchCountA(session, rv=rv)
        tmv.execute(timedelta(minutes=5))
        

    main()