#!/bin/bash

# SCRIPTNAME="$0"
# SCRIPTDIR="$(dirname -- "$( readlink -f -- "$0")")"

touch /tmp/usb.lock


cd /usbdrive || exit 1

ls | grep -e 'avi' -e 'mkv' | grep -v '.enc' | parallel -v -r --eta --jobs 2 'if [ ! -e "/usbdrive/{}.enc" ] ; then flock /tmp/usb.lock cp {} /tmp/{} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{}.enc /tmp/{} && flock /tmp/usb.lock cp /tmp/{}.enc /usbdrive/{}.enc && rm /tmp/{} /tmp/{}.enc ; fi ' 2>&1 | tee /home/edge/enc_from_usb_to_usb.stdout_and_stderr.txt
