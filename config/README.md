# About config

This folder contains environment files. One environment per boat. 

_Boat specific config files are not checked into git._ This is a precautionary procedure to prevent overwriting configs in the production environment. Boat specific config filenames are listed in `.gitignore`. 

# Using Configs

Create a new config file. It is a good idea to copy the contents from `defaults.py`.

Export the filename (with the `config/` prefix) into an environmnent variable named `ENVIRONMENT`

```
$ export ENVIRONMENT='config/queen_mary.py'
```

All code in this repository should pick up both the defaults and the the referenced `ENVIRONMENT` file for config values. Example python code:

```
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
    pass
```

# Boat specific examples:

### brancol.py

```
DEBUG=False
SECRET_KEY=''
THALOS_VIDEO_DIR="/thalos/brancol/videos"
THALOS_CAM_NAME='cam2'
VIDEO_OUTPUT_DIR='/videos'
VIDEO_PASSPHRASE_FILE='/home/edge/tnc-edge-service/scripts/secret_gpg_passphrase.txt'
THALOS_GPS_DIR="/thalos/brancol/export_gps"
BOAT_NAME='brancol'
```

### stpatrick.py

```
DEBUG=False
THALOS_VIDEO_DIR="/thalos/saintpatrick/videos"
THALOS_CAM_NAME='cam1'
VIDEO_OUTPUT_DIR='/videos'
VIDEO_PASSPHRASE_FILE='/home/edge/tnc-edge-service/scripts/secret_gpg_passphrase.txt'
SECRET_KEY=''
ONDECK_MODEL_ENGINE='/videos/model-release-v0.15-reparam-fp16-1280.engine'
THALOS_GPS_DIR="/thalos/saintpatrick/export_gps"
BOAT_NAME='stpatrick'
```
