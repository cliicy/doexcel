#!/bin/bash
## $1 /dev/sfxxxx
## $2 2 or 4 or 6 how many partitions of disk will be parted

sfxcsd=$1
number=$2
echo "will partion $1 into ${number}"

for i in `seq 1 ${number}`
do
    echo "sudo parted -s ${sfxcsd} rm ${i}"
done

if [ "${number}" = "2" ]; then
    sudo parted -s ${sfxcsd} mklabel gpt mkpart primary 0% 90%
    sudo parted -s ${sfxcsd} mkpart primary 90% 100%
fi

