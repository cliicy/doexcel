#!/bin/bash
## $1 /dev/sfxxxx
## $2 2 or 4 or 6 how many partitions of disk will be parted

sfxcss=$1
echo "will partion $1"

case $2 in 
       1) 
         echo "1 partion" 
         echo "mklabel gpt
mkpart primary 0% 100%
quit
" | sudo parted ${sfxcss}
         ;; 
       2) 
         echo "2 partion" 
         echo "mklabel gpt
yes
mkpart primary 0% 10%
mkpart primary 10% 100%
quit
" | sudo parted ${sfxcss}
         ;; 
esac 

