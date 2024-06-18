#!/bin/bash

# SCRIPTNAME="$0"
SCRIPTDIR="$(dirname -- "$( readlink -f -- "$0")")"

EXTHDPATH="/Volumes/Expansion 1"

cd "$EXTHDPATH" || exit 1


ls *.avi *.mkv | parallel -v -r --eta --jobs 2 ' flock '$SCRIPTDIR'/usb.lock cp {} '$SCRIPTDIR'/{} &&  && rm '$SCRIPTDIR'/{}' 2>&1 | tee mainsh.stdout_and_stderr.txt

ls *.enc | parallel -v -r --eta --jobs 2 ' flock '$SCRIPTDIR'/usb.lock cp {} '$SCRIPTDIR'/{} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{}.enc /tmp/{} && flock /tmp/usb.lock cp /tmp/{}.enc /usbdrive/{}.enc && rm /tmp/{} /tmp/{}.enc ; fi ' 2>&1 | tee /home/edge/enc_from_usb_to_usb.stdout_and_stderr.txt


