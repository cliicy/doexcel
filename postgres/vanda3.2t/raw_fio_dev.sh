#!/bin/bash

usage="Usage:\n\t1_prep_dev cfg_file\n\tExample: ./1_prep_dev.sh sysbench.cfg"
if [ "$1" == "" ]; then echo -e ${usage}; exit 1; fi
if [ ! -e $1 ]; then echo "can't find configuration file [$1]", exit 2; fi

# read in configurations
source $1

cpumdl=`cat /etc/tuned/active_profile`
if [ "${output_dir}" == "" ];
then
        export output_dir=${result_dir}/rawdisk-${logfolder}-`date +%Y%m%d_%H%M%S`${case_id}_${jbs}jbs_${cpumdl}_${pincpu}
fi

echo "test output will be saved in ${output_dir}"
if [ ! -e ${output_dir} ]; then mkdir -p ${output_dir}; fi

lsblk ${disk}
if [ "$?" -ne 0 ]; then echo "cannot find disk [${disk}]"; exit 3; fi

#steps="1 4 8 16 32"
#steps="1 2 3"
#for index in ${steps};
for index in {1..32};
do

./stop.sh
sudo umount ${disk}
source ./doprobvanda.sh

bsz=`expr ${index} \* 8`
fioname=${mnt_point_data##*/}

if [ "${index}" -lt "10" ]; then
    index="0"${index}
fi

outfile=${output_dir}/${index}_${fioname}.out
sudo time fio -filename=${disk} -iodepth 1 -thread -rw=randwrite -randrepeat=0 -time_based -ioengine=libaio -bs=${bsz}k -numjobs=${jbs} -runtime=${fiot} -group_reporting -name=${fioname} > ${outfile}
sleep 5

done
