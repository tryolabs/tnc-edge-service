import json

from flask import Flask
from flask_admin import Admin

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from model import Base as ModelBase, RiskVector, RiskVectorModelView, Test, TestModelView
from vector import GpsVector, FishAiEventsComeInFourHourBurstsVector

import sqlite3
from datetime import datetime, timedelta, timezone

import click

engine = create_engine("sqlite:///db.db", echo=True)
SessionMaker = sessionmaker(engine)

ModelBase.metadata.create_all(engine)


@click.command()
@click.option("--interval_hours", default=0)
@click.option("--interval_minutes", default=0)
def main(interval_hours, interval_minutes):

    n = datetime.now(tz=timezone.utc)
    d = timedelta(hours=interval_hours, minutes=interval_minutes)
    if d == timedelta(0):
        d = timedelta(hours=1)
    daterange = (n-d, n)

    with sqlite3.connect("db.db") as conn:
        with SessionMaker() as session:
            print("start of cron")
            
            q = session.query(RiskVector)
            
            all_vectors = []

            gps_vectors = []
            fishai_vectors = []

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




            for v in all_vectors:
                pass


if __name__ == '__main__':
    main()