#!/bin/bash

LEN="$(wc -l box_reupload2.done | awk '{print $1}')"

while [ "$LEN" -lt 3497 ] ; do 
  python3 box_reupload.py hq-s3-to-box
  sleep 1
  LEN="$(wc -l box_reupload2.done | awk '{print $1}')"
  echo "restarting, $LEN"
done
