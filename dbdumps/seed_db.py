# from flask import Flask
# from flask_admin import Admin
import click

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
import os

from model import Base, RiskVector, Test, T

import sqlite3

from model.internetdata import InternetData
from model import FishAiData, InternetData, GpsData

# app = Flask(__name__)
# app.config.from_object('config.defaults')

# if 'ENVIRONMENT' in os.environ:
#     app.config.from_envvar('ENVIRONMENT')


# set optional bootswatch theme
# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

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
    result = session.execute(select(InternetData))
    for inetdata in result:
        """inetdata is a tuple, because session can return multiple types per row"""
        session.delete(inetdata[0])
    result = session.execute(select(FishAiData))
    for fishaidata in result:
        """fishaidata is a tuple, because session can return multiple types per row"""
        session.delete(fishaidata[0])
    session.commit()


@click.command()
@click.option('--cleardb', default=False, is_flag=True)
@click.option('--dbname', default="edge")
@click.option('--dbuser', default="edge")
@click.option('--force', default=False, is_flag=True)
def cli(cleardb, dbname, dbuser, force):

    if not force :
        import sys
        print("This script is deprecated! run `venv/bin/alembic upgrade head` instead.")
        print("if you really want to run this script, rerun with --force")
        sys.exit(1)
    
    # engine = create_engine("sqlite:///db.db", echo=True)
    engine = create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    SessionMaker = sessionmaker(engine)
    session = SessionMaker()
    if cleardb:
        clear_db(session)
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # admin = Admin(app, name='Risk Assesment', template_mode='bootstrap3')


if __name__ == "__main__":
    cli()
