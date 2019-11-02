#!/bin/bash

sh fs_fio_dev.sh sysbench-cfg/benchmark.cfg;sh raw_fio_dev.sh sysbench-cfg/benchmark.cfg

pushd /opt/app/benchmark/postgresql/intel3.2t 
sh fio_fs_rd.sh
popd
