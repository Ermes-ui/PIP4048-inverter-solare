#!/bin/bash
cd /opt/ermes-ui/
while true
do
  echo $(date)
  echo Running SP5000 Daemon
  /usr/bin/python2 /opt/ermes-ui/SP5000-V2.py
  echo Died
done
