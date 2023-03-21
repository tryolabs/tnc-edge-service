

scriptdir="$(dirname -- "$( readlink -f -- "$0")")"

cd "$scriptdir/.."

if ! [ -e ./venv/bin/activate ] ; then
  python3 -m venv venv
fi

