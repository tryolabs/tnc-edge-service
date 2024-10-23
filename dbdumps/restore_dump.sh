#!/bin/bash

SCRIPTNAME="$0"
SCRIPTDIR="$(dirname -- "$(readlink -f -- "$0")")"

function help {
   echo "usage: $SCRIPTNAME [--dbuser USER] [--dbname NAME] [DUMPFILE]"
   echo "  DBDUMP_FILENAME defaults to the latest dumpfile, sorted by filename"
   exit 1
}

DBNAME=edge
DBUSER=edge

DUMPFILE="$(ls $SCRIPTDIR/*.pgdump | sort | tail -n 1)"

while (("$#")); do
   case $1 in
   --dbuser)
      shift && DBUSER="$1" || help
      ;;
   --dbname)
      shift && DBNAME="$1" || help
      ;;
   *)
      if [ -e "$1" ]; then
         DUMPFILE="$1"
      else
         echo "file does not exist"
         exit 1
      fi
      ;;
   esac
   shift
done

psql -U "$DBUSER" "$DBNAME" <$DUMPFILE
