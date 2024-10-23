#!/bin/bash

LEN="$(wc -l box_reupload3.done | awk '{print $1}')"

while [ "$LEN" -lt 4837 ]; do
  python3 box_reupload.py hq-s3-to-box --done-filename box_reupload3.done dp.riskedge.fish 'TNC EDGE Trip Video Files/Saint Patrick/alt_hd_upload/'
  sleep 1
  LEN="$(wc -l box_reupload3.done | awk '{print $1}')"
  echo "restarting, $LEN"
done
