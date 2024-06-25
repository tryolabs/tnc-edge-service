# About vector

This folder contains Vector classes. 

Vectors are small algorithms that generate or transform data in real time on the vessel. The term is derived from “threat vector” in the computer security ﬁeld, where speciﬁc aspects of a broad space can be evaluated independently and combined in novel ways to achieve a goal.

Multiple vectors were built for this project. Each vector is independent and covers a unique aspect of data on the boat. Vectors access recent data, analyze the data, and output a score.

### Vector code interface

The Vector code interface is not explicitly defined with a code definition. The vector code interface uses the "duck typing" paradigm, which takes advantage of Python's dynamic typing for runtime class checking and subsequent method calls. This paradigm is easy to develop, but comes at the cost of type safety.

The vector code interface contains the following methods:

```
class MyVector():
  # class is instantiated from DB rows in the `vectors` table.
  # The session grants access to 
  def __init__(self, s: session, rv) -> None:
    self.session = s
    self.rv = rv
    # The `rv.configblob` is a json string populated from a field in the DB
    confblob = json.loads(rv.configblob)
    self.my_config_value = confblob['key_in_json_blob']

  # this method is called by a scheduler at the expected_timedelta. The execute code should determine its own datetime range.
  # This method should create and commit a Test instance to the DB
  def execute(self, expected_timedelta):
    datetime_to = datetime.now(tz=timezone.utc)
    datetime_from = datetime_to - expected_timedelta
    pass
    t = Test(name="MyVector run", vector=self.rv, score=0)
    self.session.add(t)
    self.session.commit()
```

### Vector tests

Vector tests are built into vector files. They are not unified with a test framework in the project root. Vector tests in this project do not produce test reports.

The following code makes a vector runnable as a test from the cli:

```
# test by running directly with `python3 -m vector.fname`
if __name__ == '__main__':
  import os
  from flask.config import Config as FlaskConfig
  flaskconfig = FlaskConfig(root_path='')

  flaskconfig.from_object('config.defaults')
  if 'ENVIRONMENT' in os.environ:
      flaskconfig.from_envvar('ENVIRONMENT')
  import click

  @click.command()
  @click.option('--dbname', default=flaskconfig.get('DBNAME'))
  @click.option('--dbuser', default=flaskconfig.get('DBUSER'))
  def main(dbname, dbuser):
    import sqlalchemy as sa
    from sqlalchemy.orm import sessionmaker
    engine = sa.create_engine("postgresql+psycopg2://%s@/%s"%(dbuser, dbname), echo=True)
    SessionMaker = sessionmaker(engine)
    Base.metadata.create_all(engine)
    with SessionMaker() as s:
      rv = RiskVector()
      rv.id = -1
      rv.name = 'MyVector'
      rv.schedule_string = 'every 500 weeks'
      rv.configblob = '{"key_in_json_blob":True}'
      f = MyVector(s, rv)
      f.execute(timedelta(weeks=500))

  main()
      
```

## Files

Not all vectors in this folder are used in production. 

`tegrastats` was partially developed, but never finished or deployed in production.

`FishAiEventsComeInFourHourBurstsVector` was implemented for cocoannotation json files, but was not updated to use edge data, and its parameters could not be not tuned to produce usable results for this project. 

Several concepts for vectors did not make it to implementation. For example, the concept of comparing elog counts with ai counts was not be implemented because the numbers were significantly off and because we didn't have a starting dataset to define a relationship.
