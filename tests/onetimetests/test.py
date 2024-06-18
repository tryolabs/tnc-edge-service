import os
from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')


import sqlalchemy as sa
from model import Base as ModelBase, DeckhandEventView
from sqlalchemy.orm import sessionmaker as SessionMaker
sa_engine = sa.create_engine("postgresql+psycopg2://ericfultz@/edge", echo=True)
sessionmaker = SessionMaker(sa_engine)
ModelBase.metadata.create_all(sa_engine)
session = sessionmaker()
q = session.query(DeckhandEventView)
for r in q:
    print(r)
