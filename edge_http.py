import click

from flask import Flask, g
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import os


app = Flask(__name__)

app.config.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    app.config.from_envvar('ENVIRONMENT')

# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://%s@/%s"%(app.config['DBUSER'], app.config['DBNAME'])

# engine = create_engine("postgresql+psycopg2://%s@/%s"%(app.config['DBUSER'], app.config['DBNAME']), echo=True)

# SessionMaker = scoped_session(sessionmaker(bind=engine))
db = SQLAlchemy()
db.init_app(app)

from model import *
from vector import GpsVector

with app.app_context():
    # Base.metadata.create_all(engine)
    db.metadata.create_all(db.engine)
    
    from alembic import command, config
    cfg = config.Config("alembic.ini")
    command.upgrade(cfg, "head")


from api import deckhand
app.register_blueprint(deckhand, url_prefix='/deckhand')


admin = Admin(app, name='Risk Assesment', template_mode='bootstrap3')


# work with session
admin.add_view(RiskVectorModelView(db.session))
admin.add_view(TestModelView(db.session))
admin.add_view(ModelView(GpsData, db.session))
admin.add_view(ModelView(FishAiData, db.session))
admin.add_view(InternetDataView(db.session))
admin.add_view(ModelView(DeckhandEvent, db.session))

admin.add_view(ModelView(BoatSchedule, db.session))


@click.command()
@click.option('--port', default=50000)
def serve(port):
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    serve()
