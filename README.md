# Installation

## Development environment

Install python requirements with `pip` and `requirements.txt`. venv is suggested. 

```
$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

Build your own local postgres database. Most scripts allow a custom DB name (default `edge`) and a custom username (default `edge`).

## Production environment

This project is built to run on the edge on NVidia Jetson hardware. The systems run NVidia's Linux4Tegra distribution.

The Specific hardware models are:
 - `reComputer J4012 NVIDIA Jetson Orin™ NX 16GB` 
 - `reComputer J2021 NVIDIA Jetson Xavier NX 8GB`

Installation is handled by two bash scripts. These scripts are idempotent and check for some fatal errors if preconditions are not met. The scripts also include optional arguments, use `--help` for details.

Run `scripts/system_install.sh`

Run `scripts/app_install.sh`

# Folders

See nested README.md

# Files

## Config

Some files in this root folder exist to support libraries, tools, or environments:

- .gitignore
  - removes development clutter (automatically gerated files) from this git repository
  - files beginning with `secret_` are ignored. Used for programatic access of passwords and other secrets.
- alembic.ini
  - Sets up the alembic library which is in the alembic folder
- db.py
  - Old style of DB import for root SQLAlchemy. Still in use by FlaskAdmin App
- requirements.txt
  - Used for python pip

## Commands

These files in this root folder are standalone commands and entry-points for the microservices of the project:

- edge_http.py
  - Primary entrypoint for the HTTP server on the edge.
  - Runs a FlaskAdmin App that’s connected to the local DB
  - Hosts the Deckhand data api
- gps_fetch.py
  - Primary entry point for managing gps data
  - Runs a task on a schedule to scan THALOS network drive for gps data
  - Copies gps data to the local postgres db
- reencode.py
  - Primary entry point for reencoding video files
  - Runs a task on a schedule to reencode video files after they are copied from THALOS
  - Uses the nvidia hardware video encoder with  GST 
  - Reduces localdisk space used by about 5x
- run_aifish.py
  - Primary entry point for managing AI.Fish model input and output
  - Runs tasks on a schedule to copy video files to model as input
  - Runs tasks on a schedule to monitor model output files
- run_ondeck.py
  - Primary entry point for managing OnDeck model input and output
  - Runs tasks on a schedule to copy video files to model as input
  - Runs tasks on a schedule to monitor model output files
- s3_uploader.py
  - Primary entry point for uploading data to the cloud
  - Runs a task on a schedule to copy postgres tables into S3
  - Copied with the postrgres ‘COPY csv’ feature
  - Keeps track of its latest upload in the s3uploads table
- vector_schedule.py
  - Primary entry point for vectors running on the boat
  - Instantiates vectors from DB and starts the scheduler
- video_fetch.py
  - Primary entry point for managing video files
  - Runs a task on a schedule to scan THALOS network drive for video files
  - Copies video files to the local drive


## Additional Info

Please see the TNC [box.com final-products folder](app.box.com/folder/255558380555) for more info about the project.
