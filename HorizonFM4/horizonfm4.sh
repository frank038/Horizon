#!/bin/bash
thisdir=$(dirname "$0")
cd $thisdir

# chromium hack
DOWNLOAD=`xdg-user-dir DOWNLOAD`

if [[ "$@" = "." && -d "$DOWNLOAD" ]]; then
  NEWFILE=`ls -Art $DOWNLOAD | tail -n 1`
  python3 HorizonFM4.py "$DOWNLOAD/$NEWFILE" &
else
  python3 HorizonFM4.py "$@" &
fi

cd $HOME
