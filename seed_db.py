# from flask import Flask
# from flask_admin import Admin
import click

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
import os

from model import Base, RiskVector, Test, T

import sqlite3

from model.gpsdata import GpsData
engine = create_engine("sqlite:///db.db", echo=True)
SessionMaker = sessionmaker(engine)

# app = Flask(__name__)
# app.config.from_object('config.defaults')

# if 'ENVIRONMENT' in os.environ:
#     app.config.from_envvar('ENVIRONMENT')


# set optional bootswatch theme
# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'


Base.metadata.create_all(engine)

def clear_db(session: Session):
    result = session.execute(select(Test))
    for t in result:
        """t is a tuple, because session can return multiple types per row"""
        session.delete(t[0])
    result = session.execute(select(RiskVector))
    for rv in result:
        """rv is a tuple, because session can return multiple types per row"""
        session.delete(rv[0])
    result = session.execute(select(GpsData))
    for gpsdata in result:
        """gpsdata is a tuple, because session can return multiple types per row"""
        session.delete(gpsdata[0])
    session.commit()


@click.command()
@click.option('--cleardb', default=False, is_flag=True)
def cli(cleardb):
    
    with sqlite3.connect("db.db") as conn:
        c = conn.cursor()  # cursor

        # admin = Admin(app, name='Risk Assesment', template_mode='bootstrap3')


        # bind an individual session to a connection

        # with engine.connect() as connection:
        #     with Session(bind=connection) as session:
        with SessionMaker() as session:
            if cleardb:
                clear_db(session)
            objs = {
                "rvs": [
                    {
                        "name": "AI High Risk Species ID",
                        "id": 1},
                    {
                        "name": "Total Catch Count Parity",
                        "id": 2},
                    {
                        "name": "Target Catch Count Parity",
                        "id": 3},
                    {
                        "name": "ETP Catch Count Parity",
                        "id": 4},
                    {
                        "name": "Lead Type",
                        "id": 5},
                    {
                        "name": "Hook Type",
                        "id": 6},
                    {
                        "name": "AI ETP interactions",
                        "id": 7},
                    {
                        "name": "AI Bycatch Total",
                        "id": 8},
                    {
                        "name": "Past Risk Score",
                        "id": 9},
                    {
                        "name": "eLog Reported Issues",
                        "id": 10},
                    {
                        "name": "EM Health Check",
                        "id": 11},
                    {
                        "name": "GpsVector",
                        "id": 12,
                        "configblob": "{\"boundary_vertices\":[[36.9756611, -122.0273566],[36.9758839, -122.0255113],[36.9736554, -122.0240521],[36.9694039, -122.0231509],[36.9686324, -122.0227218],[36.9683924, -122.0248246],[36.9690267, -122.0263481],[36.9734497, -122.0270348]]}"
                    },
                    {
                        "name": "GpsVector",
                        "id": 13,
                        "configblob": "{\"boundary_vertices\":[[40.741895, -73.989308],[7.779557356666465, -66.23373040714596],[-2.0933860877580064, -129.51233698413918],[49.89708418179586, -148.18616354042646]]}"
                    },
                    {
                        "name": "ETP Fate",
                        "id": 14}
                ],
                "ts": [
                    {
                        "name": "t1",
                        "type": T.one,
                        "vector_id": 1
                    },
                    {
                        "name": "t2",
                        "type": T.one,
                        "vector_id": 1
                    },
                    {
                        "name": "t3",
                        "type": T.one,
                        "vector_id": 2
                    }
                ],
                "gpsdata": [
                    {
                        "sentence": "$GPGGA,210230,3855.4487,N,09446.0071,W,1,07,1.1,370.5,M,-29.5,M,,*7A"
                    },
                    {
                        "sentence": "$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,130495,003.8,E*69",
                    }
                ]
            }
            print(objs["rvs"])
            to_add = list(map(lambda rv: RiskVector(**rv), objs["rvs"]))
            print(to_add)
            session.add_all(to_add)
            session.add_all(list(map(lambda ts: Test(**ts), objs["ts"])))
            session.add_all(list(map(lambda gpsdata: GpsData(**gpsdata), objs["gpsdata"])))
            session.commit()

if __name__ == "__main__":
    cli()
