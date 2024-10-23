#!/bin/bash

scriptdir="$(dirname -- "$(readlink -f -- "$0")")"

cd "$scriptdir/.." || exit

USERNAME="$(whoami)"
USERHOME="/home/$USERNAME"
WORKINGDIR="$USERHOME/tnc-edge-service"

cd "$WORKINGDIR" || exit

if ! [ -e ./venv/bin/activate ]; then
  python3 -m venv venv
fi

if [ "$VIRTUAL_ENV" != "$(pwd)/venv" ]; then
  if [ "x$VIRTUAL_ENV" != "x" ]; then
    deactivate
  fi
  source ./venv/bin/activate
fi

pip install -r requirements.txt

PROD_CONF_FILE="$WORKINGDIR/config/prod.py"

if ! [ -e "$PROD_CONF_FILE" ]; then
  echo "DEBUG=False" >>"$PROD_CONF_FILE"
fi

if ! grep -q -E "^SECRET_KEY=" "$PROD_CONF_FILE"; then
  echo "creating secret_key in prod config"
  echo "SECRET_KEY='$(dd if=/dev/urandom count=1 | base64 | tr -d '+/Il10O' | fold -w 32 | head -n 1)'" >>"$PROD_CONF_FILE"
fi
