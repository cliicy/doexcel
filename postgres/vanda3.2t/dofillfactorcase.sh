#!/bin/bash
####fillfact100
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg 
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg



####fillfact75
sleep 10
#cp -f ./sysbench-cfg/ff75_benchmark.cfg ./sysbench-cfg/benchmark.cfg
sed -i s/fillfact=100/fillfact=75/ ./sysbench-cfg/benchmark.cfg
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg


####fillfact50
sleep 10
#cp -f ./sysbench-cfg/ff50_benchmark.cfg ./sysbench-cfg/benchmark.cfg
sed -i s/fillfact=75/fillfact=50/ ./sysbench-cfg/benchmark.cfg
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg

#cp -f ./sysbench-cfg/ori_benchmark.cfg ./sysbench-cfg/benchmark.cfg
#sh  dointel.sh
