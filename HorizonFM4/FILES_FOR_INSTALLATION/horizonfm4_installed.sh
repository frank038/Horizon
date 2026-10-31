#!/bin/bash

cd /usr/share/HorizonFM4

# chromium hack
DOWNLOAD=`xdg-user-dir DOWNLOAD`
if [[ "$@" = "." && -d "$DOWNLOAD" ]]; then
  NEWFILE=`ls -Art $DOWNLOAD | tail -n 1`
  python3 /usr/share/HorizonFM4/HorizonFM4.py "$DOWNLOAD/$NEWFILE" &
else
  python3 /usr/share/HorizonFM4/HorizonFM4.py "$@" &
fi
