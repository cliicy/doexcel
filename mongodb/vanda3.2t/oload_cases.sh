#!/bin/bash

#compression_list="none snappy zlib"
#compression_list="none"
compression_list="snappy"
for cmp in ${compression_list};
do
#do loading with case.cfg
export app_cfg=`pwd`/cfg/${cmp}.cnf
export output_dir=

./1_prep_dev.sh ./cfg/case.cfg
./2_initdb.sh   ./cfg/case.cfg
./3_run.sh      ./cfg/case.cfg

source ./output.dir
source ../lib/bench-lib
ssd_name=$(basename "$PWD")
compname=${app_cfg##*/}
generate_benchinfo ${ssd_name} ${compname%.cnf} ${output_dir}

done


#sh oloadsnappy_lf8k.sh
