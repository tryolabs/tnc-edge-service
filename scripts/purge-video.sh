#!/bin/bash

if [ "$(du -s /videos/*.avi | awk '{total += $1 }; END { print total}')" -gt 60000000 ] ; then
    ls -tr /videos/*.avi | head | xargs rm
fi

if [ "$(du -s /videos/*_reenc.mkv | awk '{total += $1 }; END {print total}')" -gt 180000000 ] ; then
    ls -tr /videos/*_reenc.mkv | head | xargs rm
fi
