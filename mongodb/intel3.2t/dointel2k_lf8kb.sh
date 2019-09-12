#!/bin/bash

workloads="load u100 r50_u50 r90_u10"
for wkl in ${workloads};
do
sed -i s/recordcount=4294967296/recordcount=1073741824/ ./workload/${wkl}
sed -i s/fieldlength=128/fieldlength=512/ ./workload/${wkl}
done

sed -i s/leaf_page_max=32KB/leaf_page_max=8KB/ ./cfg/zlib.cnf
sh split_loadrun-cases.sh
