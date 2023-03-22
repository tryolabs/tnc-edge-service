

scriptdir="$(dirname -- "$( readlink -f -- "$0")")"

cd "$scriptdir/.."

if ! [ -e ./venv/bin/activate ] ; then
  python3 -m venv venv
fi


if [ "$VIRTUAL_ENV" != "$(pwd)/venv" ] ; then
  if [ "x$VIRTUAL_ENV" != "x" ] ; then
    deactivate
  fi
  source venv/bin/activate
fi

pip install -r requirements.txt


