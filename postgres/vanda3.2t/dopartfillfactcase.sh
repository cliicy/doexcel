#!/bin/bash

####fillfact50
sleep 10
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg

#cp -f ./sysbench-cfg/ori_benchmark.cfg ./sysbench-cfg/benchmark.cfg
sh  dointel.sh
