#!/bin/bash

usage="Usage:\n\t1_prep_dev cfg_file\n\tExample: ./1_prep_dev.sh sysbench.cfg"
if [ "$1" == "" ]; then echo -e ${usage}; exit 1; fi
if [ ! -e $1 ]; then echo "can't find configuration file [$1]", exit 2; fi

# read in configurations
source $1

lsblk ${disk}
if [ "$?" -ne 0 ]; then echo "cannot find disk [${disk}]"; exit 3; fi

# stop mysql service first, since it my occupy the disk
./stop.sh

# prepare the mount point and other folders
if [ ! -e ${mnt_point_data} ]; then sudo mkdir -p ${mnt_point_data}; fi
#if [ ! -e ${mnt_point_data_pg} ]; then sudo mkdir -p ${mnt_point_data_pg}; fi

sudo umount ${disk}
sudo umount ${diskp1}
sudo umount ${diskp2}

sudo mkfs.${fs_type} -f ${disk}
sh csdpt.sh ${disk} 2
#sudo mkfs -t ${fs_type} -f ${disk}
sudo mkfs.${fs_type} -f ${diskp2}
#sudo mount ${diskp1} ${mnt_opt} ${mnt_point_data_pg}
