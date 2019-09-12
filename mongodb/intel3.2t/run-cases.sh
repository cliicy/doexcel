#!/bin/bash

compression_list="none snappy zlib"
for cmp in ${compression_list};
do
export app_cfg=`pwd`/cfg/${cmp}.cnf

./1_prep_dev.sh ./cfg/case.cfg
./2_initdb.sh   ./cfg/case.cfg
./3_run.sh      ./cfg/case.cfg
done
