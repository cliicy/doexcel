#!/bin/bash
####fillfact100
sh dotpcccase.sh

####fillfact75
sleep 10
sed -i s/fillfact=100/fillfact=75/ ./sysbench-cfg/benchmark.cfg
sh dotpcccase.sh

sed -i s/fillfact=75/fillfact=100/ ./sysbench-cfg/benchmark.cfg
