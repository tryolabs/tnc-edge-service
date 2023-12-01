#!/bin/bash

SCRIPTNAME="$0"
SCRIPTDIR="$(dirname -- "$( readlink -f -- "$0")")"

EXTHDPATH="/Volumes/Expansion 1"

cd "$EXTHDPATH" || exit 1

for i in *.avi.enc *.avi.done.enc ; do 
  if grep -q "$i" "$SCRIPTDIR/done.txt" ; then
    continue
  fi
  bname="$(basename "$i")"
  cname="${bname%*.enc}"
  boatname="${cname%%_*}"
  dtname="${cname#*_}"
  if [ 'saintpatrick' == "$boatname" ] ; then
    echo "$cname,Saint Patrick,$dtname"
  else
    echo "$cname","${boatname^}","$dtname"
  fi
done | parallel -v -r --eta --jobs 6 --colsep "," 'flock '$SCRIPTDIR'/usb2.lock cp {1}.enc '$SCRIPTDIR'/{1}.enc && gpg -d --batch -o '$SCRIPTDIR'/{1} '$SCRIPTDIR'/{1}.enc && aws s3 --profile AWSAdministratorAccess-867800856651 cp '$SCRIPTDIR'/{1} "s3://dp.riskedge.fish/TNC EDGE Trip Video Files/"{2}"/alt_hd_upload/{3}" && flock '$SCRIPTDIR'/done.lock echo {1}.enc >> '$SCRIPTDIR'/done.txt && rm '$SCRIPTDIR'/{1} '$SCRIPTDIR'/{1}.enc' 2>&1 

exit 0

for i in *.avi *.mkv ; do 
  if grep -q "$i" "$SCRIPTDIR/done.txt" ; then
    continue
  fi
  bname="$(basename "$i")"
  boatname="${bname%%_*}"
  dtname="${bname#*_}"
  if [ 'saintpatrick' == "$boatname" ] ; then
    echo "$bname","Saint Patrick","$dtname"
  else
    echo "$bname","${boatname^}","$dtname"
  fi
done | parallel -v -r --eta --jobs 6 --colsep "," --dry-run 'flock '$SCRIPTDIR'/usb2.lock cp {1} '$SCRIPTDIR'/{1} && aws s3 --profile AWSAdministratorAccess-867800856651 cp '$SCRIPTDIR'/{1} "s3://dp.riskedge.fish/TNC EDGE Trip Video Files/"{2}"/alt_hd_upload/{3}" && flock '$SCRIPTDIR'/done.lock echo {1} >> '$SCRIPTDIR'/done.txt && rm '$SCRIPTDIR'/{1}' 2>&1 

exit 0

ls *.avi *.mkv | parallel -v -r --eta --jobs 2 ' flock '$SCRIPTDIR'/usb.lock cp {} '$SCRIPTDIR'/{} &&  && rm '$SCRIPTDIR'/{}' 2>&1 | tee mainsh.stdout_and_stderr.txt

ls *.enc | parallel -v -r --eta --jobs 2 ' flock '$SCRIPTDIR'/usb.lock cp {} '$SCRIPTDIR'/{} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{}.enc /tmp/{} && flock /tmp/usb.lock cp /tmp/{}.enc /usbdrive/{}.enc && rm /tmp/{} /tmp/{}.enc ; fi ' 2>&1 | tee /home/edge/enc_from_usb_to_usb.stdout_and_stderr.txt



exit 0

touch /tmp/usb.lock /tmp/network.lock

find /thalos/brancol/videos/cam{1,2}/{15,16,17,18,19,20,21,22,23,24}-10-2023 -name '*.avi.done' | python3 -c 'from datetime import datetime; import sys; from pathlib import Path; [print( line.strip(), Path(line.strip()).parents[4].name+"_"+datetime.strptime(Path(line.strip()).name[0:16], "%d-%m-%Y-%H-%M").strftime("%Y%m%dT%H%M00Z")+"_"+Path(line.strip()).parents[2].name+".avi") for line in sys.stdin.readlines() ]' | parallel -v -r --eta --jobs 4 --colsep " " 'if [ ! -e "/usbdrive/{2}.enc" ] ; then flock /tmp/network.lock cp {1} /tmp/{2} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{2}.enc /tmp/{2} && flock /tmp/usb.lock cp /tmp/{2}.enc /usbdrive/{2}.enc && rm /tmp/{2} /tmp/{2}.enc ; fi '



echo "select original_path from video_files where start_datetime > '2023-10-16 16:45:00Z' order by start_datetime asc;" | psql -t | awk 'NF' | python3 -c 'from datetime import datetime; import sys; from pathlib import Path; [print( line.strip(), Path(line.strip()).parents[4].name+"_"+datetime.strptime(Path(line.strip()).name[0:16], "%d-%m-%Y-%H-%M").strftime("%Y%m%dT%H%M00Z")+"_"+Path(line.strip()).parents[2].name+".avi") for line in sys.stdin.readlines() ]' | parallel -v -r --eta --jobs 4 --colsep " " 'if [ ! -e "/usbdrive/{2}.enc" ] ; then flock /tmp/network.lock cp {1} /tmp/{2} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{2}.enc /tmp/{2} && flock /tmp/usb.lock cp /tmp/{2}.enc /usbdrive/{2}.enc && rm /tmp/{2} /tmp/{2}.enc ; fi '



cd /usbdrive ;
ls | grep -e 'avi' -e 'mkv' | grep -v '.enc' | parallel -v -r --eta --jobs 2 'if [ ! -e "/usbdrive/{}.enc" ] ; then flock /tmp/usb.lock cp {} /tmp/{} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{}.enc /tmp/{} && flock /tmp/usb.lock cp /tmp/{}.enc /usbdrive/{}.enc && rm /tmp/{} /tmp/{}.enc ; fi ' 2>&1 | tee /home/edge/enc_from_usb_to_usb.stdout_and_stderr.txt


echo "select original_path from video_files where start_datetime > '2023-10-28 13:50:00Z' order by start_datetime asc;" | psql -t | awk 'NF' | python3 -c 'from datetime import datetime; import sys; from pathlib import Path; [print( line.strip(), Path(line.strip()).parents[4].name+"_"+datetime.strptime(Path(line.strip()).name[0:16], "%d-%m-%Y-%H-%M").strftime("%Y%m%dT%H%M00Z")+"_"+Path(line.strip()).parents[2].name+".avi") for line in sys.stdin.readlines() ]' | parallel -v -r --eta --jobs 4 --colsep " " 'if [ ! -e "/usbdrive/{2}.enc" ] ; then flock /tmp/network.lock cp {1} /tmp/{2} && gpg -e -z 0 --batch -r edgedevice -o /tmp/{2}.enc /tmp/{2} && flock /tmp/usb.lock cp /tmp/{2}.enc /usbdrive/{2}.enc && rm /tmp/{2} /tmp/{2}.enc ; fi '

