#!/bin/bash

#compression_list="none snappy zlib"
compression_list="none"
for cmp in ${compression_list};
do
#do loading with case.cfg
export app_cfg=`pwd`/cfg/${cmp}.cnf

#do running with run_case.cfg
#export app_cfg=`pwd`/cfg/run_${cmp}.cnf
./3_run.sh      ./cfg/run_case.cfg

source ../lib/bench-lib
ssd_name=$(basename "$PWD")
compname=${app_cfg##*/}
generate_benchinfo ${ssd_name} ${compname%.cnf} ${output_dir}

done
