import json
import io

from flask import Flask
from flask_admin import Admin

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import os

from model import Base as ModelBase, RiskVector, RiskVectorModelView, Test, TestModelView
from vector import GpsVector, FishAiEventsComeInFourHourBurstsVector, InternetVector, EquipmentOutageAggVector

import sqlite3
from datetime import datetime, timedelta, timezone

import click

import schedule
import re
import time
import string


from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')


import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket('51-gema-dev-dp-raw')


csvprintable=string.printable
csvprintable = csvprintable[0:1+csvprintable.index("\t")]
csvprintable = csvprintable.replace(',', '')
def csvfilter(s):
    return ''.join(filter(lambda c: c in csvprintable, s))

def export_method_with_sqlalchemy_models(session: Session):

    try:
        now = datetime.now()

        result = session.query(Test)\
            .where(Test.datetime_from > now - timedelta(days=13), Test.vector_id == 2)\
            .order_by(Test.datetime.desc())\
            .limit(1).all()
        rows = list(result)
        if len(rows) > 0:
            
            body = io.BytesIO()
            body.write((','.join([column.name for column in Test.__mapper__.columns]) + '\n').encode())
            [body.write((','.join([str(getattr(row, column.name)) for column in Test.__mapper__.columns]) + '\n').encode()) for row in rows]
            bucket.put_object(Key="tnc_edge/"+Test.__tablename__+"/"+str(int(now.timestamp()))+".csv", Body=body.getvalue())
    except Exception as e:
        print("Error: exception in s3 uploader", e)

def s3uploader(cpool, boat, ver):

    tables = [
        'deckhandevents',
        'fishaidata',
        'gpsdata',
        'internetdata',
        'deckhandevents_mostrecentlonglineevent_jsonextracted',
        'tests',
        'video_files',
    ]

    conn: psycopg2.connection = cpool.getconn()
    try:
        with conn.cursor() as cur:
            for table in tables:
                # print(table)
                cur.execute("SELECT column_name FROM information_schema.columns \
                            WHERE table_name = %s order by ordinal_position;", (table,))
                columns = cur.fetchall()
                
                cur.execute("select max(a.max), CURRENT_TIMESTAMP from ( \
                                select max(s3uploads.datetime), CURRENT_TIMESTAMP \
                                from s3uploads where tablename = %s group by tablename \
                                union select timestamp with time zone '1970-01-01' as max, CURRENT_TIMESTAMP \
                            ) a;", (table,))
                dates = cur.fetchone()



                if table == 'video_files':
                    cur.execute('select * from video_files where start_datetime > %s and start_datetime <= %s;', (dates[0], dates[1]))
                else:
                    cur.execute('select * from '+table+' where datetime > %s and datetime <= %s;', (dates[0], dates[1]))


                rows = cur.fetchall()
                body = io.BytesIO()
                body.write((','.join([column[0] for column in columns]) + '\n').encode())
                [body.write((','.join([csvfilter(str(value)) for value in row]) + '\n').encode()) for row in rows]

                bucket.put_object(Key="tnc_edge/"+boat+"_"+ver+"_"+table+"/"+str(int(dates[1].timestamp()))+".csv", Body=body.getvalue())

                cur.execute('insert into s3uploads (datetime, tablename) values (%s, %s)', (dates[1], table,))
                conn.commit()
    finally:
        cpool.putconn(conn)



@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--boatname', default=flaskconfig.get('BOAT_NAME'))
@click.option('--dbtablesversion', default=flaskconfig.get('DB_TABLES_VERSION'))
def main(dbname, dbuser, boatname, dbtablesversion):
    
    # engine = create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    # SessionMaker = sessionmaker(engine)

    # ModelBase.metadata.create_all(engine)

    
    cpool = SimpleConnectionPool(1, 1, database=dbname, user=dbuser)
    

    def runonce(cpool, boatname, dbtablesversion):
        s3uploader(cpool, boatname, dbtablesversion)
        return schedule.CancelJob

    schedule.every(1).seconds.do(runonce, cpool, boatname, dbtablesversion)
    schedule.every(1).hours.do(s3uploader, cpool, boatname, dbtablesversion)

    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            print("sleeping for:", n)
            time.sleep(n)
        schedule.run_pending()

if __name__ == '__main__':
    main()