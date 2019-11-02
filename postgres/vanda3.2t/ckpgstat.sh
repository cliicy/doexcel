#!/bin/bash

for i in {1..1200};
do
    /opt/app/postgresql-10.10/bin/psql vandat -f pgstatements/stat.sql > ${1}/stats_${i}.out
    sleep 3
done

