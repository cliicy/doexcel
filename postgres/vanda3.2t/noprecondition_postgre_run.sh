#!/bin/bash

./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg 

./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

sh dointel.sh
