#!/bin/bash

SCRIPTNAME="$0"
SCRIPTDIR="$(dirname -- "$(readlink -f -- "$0")")"

touch /tmp/usb.lock /tmp/network.lock

echo "select original_path from video_files where start_datetime > '2023-10-16 16:45:00Z' order by start_datetime asc;" | psql -t | awk 'NF' | python3 -c 'from datetime import datetime; import sys; from pathlib import Path; [print( line.strip(), Path(line.strip()).parents[4].name+"_"+datetime.strptime(Path(line.strip()).name[0:16], "%d-%m-%Y-%H-%M").strftime("%Y%m%dT%H%M00Z")+"_"+Path(line.strip()).parents[2].name+".avi") for line in sys.stdin.readlines() ]' | parallel -v -r --eta --jobs 4 --colsep " " 'if [ ! -e "/usbdrive/{2}.enc" ] ; then flock /tmp/network.lock cp {1} /tmp/{2} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{2}.enc /tmp/{2} && flock /tmp/usb.lock cp /tmp/{2}.enc /usbdrive/{2}.enc && rm /tmp/{2} /tmp/{2}.enc ; fi '
