
SCRIPTNAME="$0"
SCRIPTDIR="$(dirname -- "$( readlink -f -- "$0")")"


DBNAME=edge
DBUSER=edge

while (( "$#" )); do
   case $1 in
      --dbuser)
         shift && DBUSER="$1" || help
         ;;
      --dbname)
         shift && DBNAME="$1" || help
         ;;
      *)
          help
          ;;
   esac
   shift
done


cd "$SCRIPTDIR/.."

if [ "$VIRTUAL_ENV" != "$(pwd)/venv" ] ; then
  if [ "x$VIRTUAL_ENV" != "x" ] ; then
    deactivate
  fi
  source venv/bin/activate
fi


python -c 'from sqlalchemy import create_engine; \
from model import Base; \
engine = create_engine("postgresql+psycopg2://'$DBUSER'@/'$DBNAME'", echo=True); \
Base.metadata.drop_all(engine); Base.metadata.create_all(engine)'
