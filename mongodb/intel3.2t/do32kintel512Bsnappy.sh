#!/bin/bash

sleep 180
sh stop.sh

workloads="load u100 r50_u50 r90_u10"
for wkl in ${workloads};
do
sed -i s/recordcount=1073741824/recordcount=4294967296/ ./workload/${wkl}
sed -i s/fieldlength=512/fieldlength=128/ ./workload/${wkl}
done

compression_list="snappy zlib"
for cmp in ${compression_list};
do
#do loading with case.cfg
export app_cfg=`pwd`/cfg/${cmp}.cnf
export output_dir=

sed -i s/leaf_page_max=8KB/leaf_page_max=32KB/ ./cfg/none.cnf
sed -i s/leaf_page_max=8KB/leaf_page_max=32KB/ ./cfg/snappy.cnf
sed -i s/leaf_page_max=8KB/leaf_page_max=32KB/ ./cfg/zlib.cnf

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
sleep 180
done

