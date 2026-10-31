#!/bin/bash
thisdir=$(dirname "$0")
cd $thisdir

python3 HorizonFM4.py trash:// &

cd $HOME
