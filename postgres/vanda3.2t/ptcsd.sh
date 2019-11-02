#!/bin/bash
## $1 /dev/sfxxxx
## $2 2 or 4 or 6 how many partitions of disk will be parted

sfxcss=$1
echo "will partion $1"


case $2 in 
       1) 
         echo "1 partion" 
         echo "mkpart primary '0%' '100%'
" | sudo parted -s ${sfxcss} mklabel gpt
         ;; 
       2) 
          sudo parted ${sfxcss} << EXIT
          mklabel gpt -s
          mkpart primary 0% 10% 
          mkpart primary 10% 100% 
          ignore
          quit
EXIT
         ;; 
esac 

