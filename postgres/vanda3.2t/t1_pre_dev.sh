#!/bin/bash

if [ "$?" -ne 0 ]; then echo "cannot find disk [${disk}]"; exit 3; fi

# stop mysql service first, since it my occupy the disk
./stop.sh
echo "aaaa"
# prepare the mount point and other folders
if [ ! -e ${mnt_point_data} ]; then sudo mkdir -p ${mnt_point_data}; fi

sudo umount ${disk}

sudo mkfs -t ${fs_type} ${disk}
sudo mount ${disk} ${mnt_point_data}

