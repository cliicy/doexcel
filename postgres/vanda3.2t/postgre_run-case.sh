#!/bin/bash
####fillfact100
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg 
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg

pushd /opt/app/benchmark/postgresql/intel3.2t
sleep 600
./dointel100.sh
popd


####fillfact75
sleep 600
sed -i s/fillfact=100/fillfact=75/ ./sysbench-cfg/benchmark.cfg
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg

pushd /opt/app/benchmark/postgresql/intel3.2t
sleep 600
sed -i s/fillfact=100/fillfact=75/ ./sysbench-cfg/benchmark.cfg
./dointel100.sh
popd


####fillfact50
sleep 600
sed -i s/fillfact=75/fillfact=50/ ./sysbench-cfg/benchmark.cfg
./1_prep_dev.sh ./sysbench-cfg/benchmark.cfg
./2_initdb.sh   ./sysbench-cfg/benchmark.cfg
./3_run.sh      ./sysbench-cfg/benchmark.cfg

./dorunwkloads.sh ./sysbench-cfg/benchmark.cfg
sed -i s/fillfact=50/fillfact=100/ ./sysbench-cfg/benchmark.cfg

pushd /opt/app/benchmark/postgresql/intel3.2t
sleep 600
sed -i s/fillfact=75/fillfact=50/ ./sysbench-cfg/benchmark.cfg
./dointel100.sh
sed -i s/fillfact=50/fillfact=100/ ./sysbench-cfg/benchmark.cfg
popd

