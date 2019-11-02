#!/bin/bash

cfg_file=$1
if [ "$1" = "" ]; then echo -e "Usage:\n\t2_initdb.sh cfg_file"; exit 1; fi
if [ ! -e ${cfg_file} ]; then echo "can't find configuration file [${cfg_file}]", exit 2; fi
source ${cfg_file}


source ./output.dir
runningwl=$2
echo "rworkload_set=${rworkload_set}" >> ${output_dir}/postgresql.opts

lastwl=`echo ${rworkload_set} | awk '{print $NF}'`
for workload in ${rworkload_set};
do
    ./3_run.sh ${cfg_file}
    runningwl=${workload}

    sleep 10
    if [ "${workload}" != "${lastwl}" ]; then
         # preparing the vacuumed-loaded data from the other disk
        ./1_prep_dev.sh ${cfg_file} 
        if [ "${app_datadir}" != "" ] && [ ! -e ${app_datadir} ];
        then
            sudo mkdir -p ${app_datadir};
        fi
        sudo chown -R `whoami`:`whoami` ${app_datadir}
        cp -r ${mnt_point_data}bk/* ${mnt_point_data}
        echo "do ${workload} and will start postgreSQL server " >${app_dbglog}
        chmod -R 0700 ${app_datadir}
        ./start.sh ${cfg_file}
        sleep 5
    fi
done

sed -i s/workload_set=${runningwl}/workload_set=prepare/ ${cfg_file} 

source ../lib/bench-lib
info=`cat ${output_dir}/ben.info | head -1`
gen_benchinfo_postgres ${info} 


