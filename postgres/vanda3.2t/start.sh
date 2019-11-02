#!/bin/bash

cfg_file=$1
if [ "$1" = "" ]; then echo -e "Usage:\n\t2_initdb.sh cfg_file"; exit 1; fi
if [ ! -e ${cfg_file} ]; then echo "can't find configuration file [${cfg_file}]", exit 2; fi
source ${cfg_file}

${app_basedir}/bin/initdb -D ${app_datadir}
cp -f ${app_pgconf} ${app_datadir}
${app_basedir}/bin/pg_ctl -D ${app_datadir} -l ${app_dbglog} start

#${app_basedir}/bin/pg_ctl restart -D ${app_datadir}
#${app_basedir}/bin/pg_ctl reload -D ${app_datadir}

for i in {1..1200};
do
    cat ${app_dbglog} | grep "database system is ready to accept connections"
    if [ $? -eq 0 ]; then echo started; sleep 10; break; fi
    echo "waiting for postgresql to start"
    sleep 3
done


#create test database for pgbench to benchmark
echo -e "create database ${dbname} 
\q" | ${app_basedir}/bin/psql postgres

