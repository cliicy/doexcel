#!/bin/bash

./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg 

pushd fio
sh ./postgre_precond.sh
rm -rf /opt/data/vanda/fio/*
popd

./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
#./onlyrun_2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

#sh dointel.sh
