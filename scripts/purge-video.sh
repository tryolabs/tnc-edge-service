#!/bin/bash

while [ "$(du -s /videos/*.avi | awk '{total += $1 }; END { print total}')" -gt 50000000 ]; do
    ls -tr /videos/*.avi | head | xargs rm
done

while [ "$(du -s /videos/*_reenc.mkv | awk '{total += $1 }; END {print total}')" -gt 150000000 ]; do
    ls -tr /videos/*_reenc.mkv | head | xargs rm
done
