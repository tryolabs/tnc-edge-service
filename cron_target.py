import json

from flask import Flask
from flask_admin import Admin

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from model import Base as ModelBase, RiskVector, RiskVectorModelView, Test, TestModelView
from vector import GpsVector, FishAiEventsComeInFourHourBurstsVector, InternetVector, EquipmentOutageAggVector

import sqlite3
from datetime import datetime, timedelta, timezone

import click



@click.command()
@click.option("--interval_hours", default=0)
@click.option("--interval_minutes", default=0)
@click.option('--dbname', default="edge")
@click.option('--dbuser', default="edge")
def main(interval_hours, interval_minutes, dbname, dbuser):
    # engine = create_engine("sqlite:///db.db", echo=True)
    engine = create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    SessionMaker = sessionmaker(engine)

    ModelBase.metadata.create_all(engine)

    n = datetime.now(tz=timezone.utc)
    d = timedelta(hours=interval_hours, minutes=interval_minutes)
    if d == timedelta(0):
        d = timedelta(hours=1)
    daterange = (n-d, n)

    with SessionMaker() as session:
        print("start of cron")
        
        q = session.query(RiskVector)
        
        all_vectors = []

        gps_vectors = []
        fishai_vectors = []
        inet_vectors = []
        eov_vectors = []

        for v in q.all():
            print("start of vector", v)
            all_vectors.append(v)
            if v.name == GpsVector.__name__:
                g = GpsVector(session, v)
                gps_vectors.append(g)
                res = g.execute(daterange, None)
                print("end of vector", res)
            if v.name == FishAiEventsComeInFourHourBurstsVector.__name__:
                f = FishAiEventsComeInFourHourBurstsVector(session, v)
                fishai_vectors.append(f)
                res = f.execute(daterange)
                print("end of vector", res)


            if v.name == InternetVector.__name__:
                f = InternetVector(session, v)
                inet_vectors.append(f)
                res = f.execute(daterange)
                print("end of vector", res)

            if v.name == EquipmentOutageAggVector.__name__:
                eov = EquipmentOutageAggVector(session, v)
                eov_vectors.append(eov)
                res = eov.execute(daterange)
                print("end of vector", res)



        for v in all_vectors:
            pass


if __name__ == '__main__':
    main()