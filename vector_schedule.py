import os
import re
import time
from datetime import timedelta

import boto3
import click
import schedule
from flask.config import Config as FlaskConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Base as ModelBase
from model import RiskVector
from vector import (
    CatchCountA,
    ElogTimeGapsVector,
    EquipmentOutageAggVector,
    FishAiEventsComeInFourHourBurstsVector,
    GpsVector,
    InternetVector,
    ThalosMountVector,
    ThalosVideosExistVector,
)

flaskconfig = FlaskConfig(root_path="")

flaskconfig.from_object("config.defaults")
if "ENVIRONMENT" in os.environ:
    flaskconfig.from_envvar("ENVIRONMENT")

s3 = boto3.resource("s3")
bucket = s3.Bucket("51-gema-dev-dp-raw")


def parse_and_schedule(vector: RiskVector, execute_func, *args):
    if not vector.schedule_string:
        return

    if m := re.match("every (\\d+) minutes", vector.schedule_string):
        d = timedelta(minutes=int(m.group(1)))
        schedule.every(int(m.group(1))).minutes.do(execute_func, d, *args)

    elif m := re.match("every (\\d+) hours", vector.schedule_string):
        d = timedelta(hours=int(m.group(1)))
        schedule.every(int(m.group(1))).hours.do(execute_func, d, *args)
    else:
        click.echo("VECTOR NOT SCHEDULED: {}".format(vector.name))


@click.command()
@click.option("--dbname", default=flaskconfig.get("DBNAME"))
@click.option("--dbuser", default=flaskconfig.get("DBUSER"))
def main(dbname, dbuser):
    # engine = create_engine("sqlite:///db.db", echo=True)
    # print(os.environ, dbuser, dbname)

    engine = create_engine("postgresql+psycopg2://%s@/%s" % (dbuser, dbname), echo=True)
    SessionMaker = sessionmaker(engine)

    ModelBase.metadata.create_all(engine)

    with SessionMaker() as session:
        print("start of cron")

        q = session.query(RiskVector)

        all_vectors = []

        gps_vectors = []
        fishai_vectors = []
        inet_vectors = []
        eov_vectors = []
        tmv_vectors = []
        tve_vectors = []
        eltg_vectors = []
        cca_vectors = []

        for v in q.all():
            print("start of vector", v)
            all_vectors.append(v)

            if v.name == GpsVector.__name__:
                g = GpsVector(session, v)
                gps_vectors.append(g)
                parse_and_schedule(v, g.execute, None)
                # print("end of vector", res)

            if v.name == FishAiEventsComeInFourHourBurstsVector.__name__:
                f = FishAiEventsComeInFourHourBurstsVector(session, v)
                fishai_vectors.append(f)
                # res = f.execute(daterange)
                # print("end of vector", res)

            if v.name == InternetVector.__name__:
                f = InternetVector(session, v)
                inet_vectors.append(f)
                parse_and_schedule(v, f.execute)
                # res = f.execute(daterange)
                # print("end of vector", res)

            if v.name == EquipmentOutageAggVector.__name__:
                eov = EquipmentOutageAggVector(session, v)
                eov_vectors.append(eov)
                parse_and_schedule(v, eov.execute)
                # res = eov.execute(daterange)
                # print("end of vector", res)

            if v.name == ThalosMountVector.__name__:
                tmv = ThalosMountVector(session, v)
                tmv_vectors.append(tmv)
                parse_and_schedule(v, tmv.execute)
                # res = eov.execute(daterange)
                # print("end of vector", res)

            if v.name == ThalosVideosExistVector.__name__:
                tve = ThalosVideosExistVector(session, v)
                tve_vectors.append(tve)
                parse_and_schedule(v, tve.execute)
                # res = eov.execute(daterange)
                # print("end of vector", res)

            if v.name == ElogTimeGapsVector.__name__:
                eltg = ElogTimeGapsVector(session, v)
                eltg_vectors.append(eltg)
                parse_and_schedule(v, eltg.execute)

            if v.name == CatchCountA.__name__:
                cca = CatchCountA(session, v)
                cca_vectors.append(cca)
                parse_and_schedule(v, cca.execute)

        for v in all_vectors:
            pass

        while 1:
            n = schedule.idle_seconds()
            if n is None:
                # no more jobs
                break
            elif n > 0:
                # sleep exactly the right amount of time
                click.echo("sleeping for: {}".format(n))
                time.sleep(n)
            schedule.run_pending()


if __name__ == "__main__":
    main()
