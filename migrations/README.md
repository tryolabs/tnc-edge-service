# About migrations

This folder is reserved for Alembic database migration scripts and configs.

# Using Alembic

Alembic is installed as one of the pip requirements.txt packages. Using a venv is suggested. Exporting the `ENVIRONMENT` config is required.

The `alembic` cli command provides a suite of tools to manage database migrations. 

Alembic migration scripts can be run forwards or backwards with `upgrade` and `downgrade`

```
(venv) $ export ENVIRONMENT="config/queen_mary.py"
(venv) $ alembic downgrade ba08d4e11cc7
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade e718ddd7c0bd -> fdfd9e708602, add_track_table
INFO  [alembic.runtime.migration] Running downgrade fdfd9e708602 -> ba08d4e11cc7, add_elog_timegap_vector_row
(venv) $ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade ba08d4e11cc7 -> fdfd9e708602, add_elog_timegap_vector_row
INFO  [alembic.runtime.migration] Running upgrade fdfd9e708602 -> e718ddd7c0bd, add_track_table
(venv) $ 
```

Alembic provides a tool that auto-generates new migration scripts from detected differences between the db schema and the python db model classes.


```
(venv) $ export ENVIRONMENT="config/queen_mary.py"
(venv) $ alembic revision --autogenerate -m new_migration_filename
```
