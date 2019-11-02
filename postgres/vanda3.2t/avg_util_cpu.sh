#!/bin/bash

pushd $1
cat csv/run.iostat.csv |cut -d ',' -f10 > run_diskutil
sed -i '1d' run_diskutil
cat run_diskutil | awk '{sum+=$1;count++}END{print "%disk-util:",sum/NR}'> avg.util_cpu

cat csv/run.iostat.cpu.csv |cut -d ',' -f4 > run_cpu
sed -i '1d' run_cpu
cat run_cpu | awk '{sum+=$1;count++}END{print "%cpu-uage:",100-sum/NR}'>> avg.util_cpu
