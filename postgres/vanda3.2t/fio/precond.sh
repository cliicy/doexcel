#!/bin/bash

dev_list=("nvme0n1" "sfdv0n1")
vendor_list=("intel" "vanda")
mkfs_opt="-t ext4"
mnt_opt=" "
mntpnt_base=/opt/data

function exit_on_error() {
    err_code=$1
    if [ "$err_code" == "" ]; then err_code=-1; fi
    if [ $err_code -ne 0 ]; then exit $err_code; fi
}

for((i=0;i<${#dev_list[@]};i++))
do
    dev_name=${dev_list[${i}]}
    dev_path=/dev/${dev_name}
    mntpnt=${mntpnt_base}/${vendor_list[${i}]}
    echo "${dev_name}"
    echo "${mntpnt}"
    echo "${mkfs_opt}"
    echo "${mnt_opt}"
    tmp_mntpnt=$(lsblk ${dev_path} | grep ${dev_name} | sed -r "s/\s+/,/g" | cut -f7 -d,)
    if [ "${tmp_mntpnt}" != "" ];
    then
        sudo umount ${dev_path}
        exit_on_error $?
    fi
    sudo mkfs ${mkfs_opt} ${dev_path}
    exit_on_error $?
    sudo mount ${mnt_opt} ${dev_path} ${mntpnt}
    exit_on_error $?
    sudo mkdir ${mntpnt}/fio
    sudo chown -R `whoami`:`whoami` ${mntpnt}/fio
done

date -Iseconds > size.txt
echo "precondition starts ..." >> size.txt
~/csd-size.sh sfdv0n1 >> size.txt
df -h /dev/nvme0n1 /dev/sfdv0n1 >> size.txt

fio jobs/precondition.fio

~/csd-size.sh sfdv0n1 >> size.txt
echo "precondition completed ..." >> size.txt
date -Iseconds >> size.txt
