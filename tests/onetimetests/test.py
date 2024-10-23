import os

import sqlalchemy as sa
from flask.config import Config as FlaskConfig
from sqlalchemy.orm import sessionmaker as SessionMaker

from model import Base as ModelBase
from model import DeckhandEventView

flaskconfig = FlaskConfig(root_path="")

flaskconfig.from_object("config.defaults")
if "ENVIRONMENT" in os.environ:
    flaskconfig.from_envvar("ENVIRONMENT")


sa_engine = sa.create_engine("postgresql+psycopg2://ericfultz@/edge", echo=True)
sessionmaker = SessionMaker(sa_engine)
ModelBase.metadata.create_all(sa_engine)
session = sessionmaker()
q = session.query(DeckhandEventView)
for r in q:
    print(r)
