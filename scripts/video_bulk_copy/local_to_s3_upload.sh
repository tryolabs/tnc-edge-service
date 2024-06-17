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

for i in *.avi *.avi.done *.mkv ; do 
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
done | parallel -v -r --eta --jobs 6 --colsep "," 'flock '$SCRIPTDIR'/usb2.lock cp {1} '$SCRIPTDIR'/{1} && aws s3 --profile AWSAdministratorAccess-867800856651 cp '$SCRIPTDIR'/{1} "s3://dp.riskedge.fish/TNC EDGE Trip Video Files/"{2}"/alt_hd_upload/{3}" && flock '$SCRIPTDIR'/done.lock echo {1} >> '$SCRIPTDIR'/done.txt && rm '$SCRIPTDIR'/{1}' 2>&1 

exit 0
