#!/bin/bash

if [ "${app_datadir}" == "" ]; then
    app_datadir=/opt/data/vanda/postgresql-10.10/
fi

if [ "${app_basedir}" == "" ]; then
    app_basedir=/opt/app/postgresql-10.10
fi

if [ -d "${app_datadir}" ]; then
    ${app_basedir}/bin/pg_ctl -D ${app_datadir} stop
fi

kill -9 `ps aux | grep -v grep | grep -e bin/postgres | cut -c 10-15`

for i in {1..100};
do
    ps aux | grep -v grep | grep -e bin/postgres
    if [ $? -ne 0 ]; then echo stopped; sleep 10; break; fi
    echo "waiting for postgresql to exit"
    sleep 3
done
