#!/bin/bash

./1_prep_dev.sh ./sysbench-cfg/quick.cfg 
./2_initdb.sh   ./sysbench-cfg/quick.cfg
./3_run.sh      ./sysbench-cfg/quick.cfg

#sh dointel.sh

sleep 5
sed -i s/fillfact=100/fillfact=75/ ./sysbench-cfg/quick.cfg
./1_prep_dev.sh ./sysbench-cfg/quick.cfg
./2_initdb.sh   ./sysbench-cfg/quick.cfg
./3_run.sh      ./sysbench-cfg/quick.cfg


sleep 5
sed -i s/fillfact=75/fillfact=50/ ./sysbench-cfg/quick.cfg
./1_prep_dev.sh ./sysbench-cfg/quick.cfg
./2_initdb.sh   ./sysbench-cfg/quick.cfg
./3_run.sh      ./sysbench-cfg/quick.cfg

sed -i s/fillfact=50/fillfact=100/ ./sysbench-cfg/quick.cfg
