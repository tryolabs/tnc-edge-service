# About models

This folder contains ORM model classes for use by the application. The ORM is SQLAlchemy. The model files are one-class-per-sql-table with columns and relationships defined in the class definition.

This folder does not contain any AI models or statistical models.

## Using the models

### Code Prerequisites 

- Every model in this folder should extend Base. 
- Every model in this folder should be added to `__init__.py`.

### Runtime Prerequisites

- Create a SQLAlchemy engine
  - `from sqlalchemy import create_engine`
  - `engine = create_engine(...)`
- Import the model Base class and connect the metadata object to the engine
  - `from model import Base as ModelBase`
  - `ModelBase.metadata.create_all(engine)`

Now any model can be imported and directly used with SQLAlchemy sessions:

```
from model import Test
SessionMaker = sessionmaker(engine)
with SessionMaker() as session:
  results = session.query(Test)
```

## SQLAlchemy ORM Styles

The SQLAlchemy project has two fully featured coding styles for creating ORM models. This project uses the declarative style. [See here for more.](https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#orm-mapping-styles)

## SQLAlchemy 1.4 vs 2.0

This project uses SQLAlchemy 1.4 because that was the maximum version supported by other python modules at the time this project locked its dependencies. 

Updating the project to SQLAlchemy 2.0 would be good and is only held back by the dev time investment. [See here for more.](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html#) All instances of `session.query()` need to be replaced with `session.execute(select())` or similar.

## Use with Flask-Admin

The Flask-Admin module has a default ModelView class to dynamically create a HTTP page+form for DB data manipulation. Any model class in this folder can be passed into the default ModelView. 

Some of the model classes in this folder extend that functionality by making their own ModelView class. e.g:

```
class InternetDataView(ModelView):
  def __init__(self, session):
    ...
```
