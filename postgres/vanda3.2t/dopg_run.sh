#!/bin/bash


source sysbench-cfg/benchmark.cfg
sh stop.sh
sudo umount ${diskp1}
sudo mkfs.${fs_type} -f ${diskp1}
sudo mount ${diskp1} ${mnt_opt} ${mnt_point_data_pg}
sh 2_initdb.sh sysbench-cfg/benchmark.cfg
sh 3_run.sh sysbench-cfg/benchmark.cfg

sh dointel.sh
