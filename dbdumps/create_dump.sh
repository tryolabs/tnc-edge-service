#!/bin/bash

SCRIPTNAME="$0"
SCRIPTDIR="$(dirname -- "$(readlink -f -- "$0")")"

function help {
   echo "usage: $SCRIPTNAME  [--dbuser USER] [--dbname NAME] "
   exit 1
}

DBNAME=edge
DBUSER=edge

while (("$#")); do
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

pg_dump --clean -U "$DBUSER" "$DBNAME" >"$SCRIPTDIR/$(date -u -Iseconds | cut -f1 -d +)Z.pgdump"
