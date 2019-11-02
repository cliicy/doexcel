#!/bin/bash

./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg 
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg


sleep 600
sed -i s/fillfact=100/fillfact=75/ ./sysbench-cfg/benchmark.cfg
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg


sleep 600
sed -i s/fillfact=75/fillfact=50/ ./sysbench-cfg/benchmark.cfg
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

sed -i s/fillfact=50/fillfact=100/ ./sysbench-cfg/benchmark.cfg

sh dointel.sh
