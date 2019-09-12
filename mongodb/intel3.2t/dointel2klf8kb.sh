#!/bin/bash

sed -i s/leaf_page_max=8KB/leaf_page_max=32KB/ ./cfg/zlib.cnf
sh split_loadrun-cases.sh; sh dointel2k_lf8kb.sh

