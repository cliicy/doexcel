#!/bin/bash

usage="Usage:\n\t1_prep_dev cfg_file\n\tExample: ./1_prep_dev.sh cfg_file"
if [ "$1" == "" ]; then echo -e ${usage}; exit 1; fi
if [ ! -e $1 ]; then echo "can't find configuration file [$1]", exit 2; fi

# read in configurations
source $1

lsblk ${disk}
if [ "$?" -ne 0 ]; then echo "cannot find disk [${disk}]"; exit 3; fi

# stop existing ycsb processes first, since it my occupy the disk
./stop.sh

tmp_mnt_point=`lsblk ${disk} | grep disk | sed -r 's/\s+/ /g' | cut -d " " -f 7`
if [ "${tmp_mnt_point}" !=  "" ]; then sudo umount ${tmp_mnt_point}; fi

# prepare the mount point and other folders
if [ ! -e ${mnt_point} ]; then sudo mkdir -p ${mnt_point}; fi
sudo mkfs -t ${fs_type} ${disk}
sudo mount ${mnt_opt} ${disk} ${mnt_point}
