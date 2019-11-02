#!/bin/bash
####fillfact100
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg 
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg
sh dotpcccase.sh

####fillfact75
sleep 10
sed -i s/fillfact=100/fillfact=75/ ./sysbench-cfg/benchmark.cfg
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg
sh dotpcccase.sh

sh  dointel.sh
