#!/bin/bash

if [ "$(du -s /videos | awk '{print $1}')" -gt 60000000 ] ; then
    ls -tr /videos/*.avi | head | xargs rm
fi
