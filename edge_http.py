import click

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from model import Base as ModelBase, RiskVector, RiskVectorModelView, Test, TestModelView, GpsData, FishAiData, InternetData, InternetDataView
from vector import GpsVector

@click.command()
@click.option('--port', default=50000)
@click.option('--dbname', default="edge")
@click.option('--dbuser', default="edge")
def serve(port, dbname, dbuser):
    # engine = create_engine("sqlite:///db.db", echo=True)
    engine = create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)

    SessionMaker = sessionmaker(engine)

    app = Flask(__name__)
    app.config.from_object('config.defaults')

    if 'ENVIRONMENT' in os.environ:
        app.config.from_envvar('ENVIRONMENT')


    # set optional bootswatch theme
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

    from api import deckhand
    app.register_blueprint(deckhand, url_prefix='/deckhand')

    ModelBase.metadata.create_all(engine)

    allvectorcode = [
        # GpsVector(SessionMaker)
    ]

    admin = Admin(app, name='Risk Assesment', template_mode='bootstrap3')


    # bind an individual session to a connection

    # with engine.connect() as connection:
    #     with Session(bind=connection) as session:
    with SessionMaker() as session:
            # work with session
            admin.add_view(RiskVectorModelView(session))
            admin.add_view(TestModelView(session))
            admin.add_view(ModelView(GpsData, session))
            admin.add_view(ModelView(FishAiData, session))
            admin.add_view(InternetDataView(session))

            app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    serve()
