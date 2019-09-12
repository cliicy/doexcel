#!/bin/bash

compression_list="none snappy zlib"
for cmp in ${compression_list};
do
#do loading with case.cfg
sleep 180
sh stop.sh
export app_cfg=`pwd`/cfg/${cmp}.cnf
export output_dir=

sed -i s/leaf_page_max=32KB/leaf_page_max=8KB/ ./cfg/none.cnf
sed -i s/leaf_page_max=32KB/leaf_page_max=8KB/ ./cfg/snappy.cnf
sed -i s/leaf_page_max=32KB/leaf_page_max=8KB/ ./cfg/zlib.cnf

./1_prep_dev.sh ./cfg/case.cfg
./2_initdb.sh   ./cfg/case.cfg
./3_run.sh      ./cfg/case.cfg

#do running with run_case.cfg
#export app_cfg=`pwd`/cfg/run_${cmp}.cnf
source ./output.dir
./3_run.sh      ./cfg/run_case.cfg

source ../lib/bench-lib
ssd_name=$(basename "$PWD")
compname=${app_cfg##*/}
generate_benchinfo ${ssd_name} ${compname%.cnf} ${output_dir}

rm -rf ./output.dir
done

