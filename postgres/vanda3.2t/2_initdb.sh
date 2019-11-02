#!/bin/bash

cfg_file=$1
if [ "$1" = "" ]; then echo -e "Usage:\n\t2_initdb.sh cfg_file"; exit 1; fi
if [ ! -e ${cfg_file} ]; then echo "can't find configuration file [${cfg_file}]", exit 2; fi
source ${cfg_file}

./stop.sh ${cfg_file}

if [ "${app_datadir}" != "" ] && [ ! -e ${app_datadir} ];
then
        sudo mkdir -p ${app_datadir};
fi
sudo chown -R `whoami`:`whoami` ${app_datadir}

if [ "${app_datadir}" != "" ] && [ ! -e ${app_datadir} ];
then
	rm -rf ${app_datadir}/*
fi

./start.sh ${cfg_file}

