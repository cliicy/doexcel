export css_util_dir=/home/tcn/software/vanda/rc_3.0.2.0-r48663/centos7.5/sfx_qual_suite/
export css_status=${css_util_dir}/css-status.sh
export initcard="./initcard.sh --blk --cl"

pushd ${css_util_dir}
sudo ./initcard.sh --blk --cl
#sudo ./initcard.sh --blk --cl  --capacity=6400
popd
