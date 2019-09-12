#!/bin/bash

pushd  /opt/app/benchmark/mongodb/vanda3.2t/
sh stop.sh

compression_list="none"
for cmp in ${compression_list};
do
#do loading with case.cfg
export app_cfg=`pwd`/cfg/${cmp}.cnf
export output_dir=

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

sh stop.sh
for cmp in ${compression_list};
do
#do loading with case.cfg
export app_cfg=`pwd`/cfg/${cmp}.cnf
export output_dir=

sed -i s/leaf_page_max=32KB/leaf_page_max=8KB/ ./cfg/none.cnf

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

popd
