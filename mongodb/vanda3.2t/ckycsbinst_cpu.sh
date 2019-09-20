#! /bin/bash

output_dir=$1
instpid_file=${output_dir}/ycsb.inst
app_basedir=$2
yscb_dir=$3
pid_limit=20
cmd=$4

ps -ef | grep -v grep | grep -e ${yscb_dir} | awk '{print $2}'> ${instpid_file}
if [ -e ${instpid_file} ]; then
    mkdir -p ${output_dir}/ycsb_pid
    pid_list=
    index=0
    for i in `cat ${instpid_file}`
    do
        if [ "${index}" == "${pid_limit}" ];then
	    #echo -e "${pid_list}\n" >> ${output_dir}/ycsb.ppid 
            index=0
            pid_list=${pid_list}"\n,${i}" 
        else
            pid_list=${pid_list}",${i}"
        fi
        index=`expr ${index} + 1`
    done
    echo -e "${pid_list}" > ${output_dir}/ycsb.ppid

    for pidlst in `cat ${output_dir}/ycsb.ppid`
    do
        pidlist=${pidlst#*,}
        if [ -n "${pidlist}" ]; then
            echo "top -b -p ${pidlist} >> ${output_dir}/ycsb_pid/ycsb.cpu & "
            top -b -p ${pidlist} >> ${output_dir}/ycsb_pid/ycsb_${cmd}.cpu & 
        fi
    done
fi

mongodb_inst=${output_dir}/mongodb.inst
ps -ef | grep -v grep | grep -e ${app_basedir}/bin/mongod | awk '{print $2}'> ${mongodb_inst}
if [ -e ${mongodb_inst} ]; then
    mkdir -p ${output_dir}/mongodb_pid
    mongo_pid_list=
    for i in `cat ${mongodb_inst}`
    do
        mongo_pid_list=${mongo_pid_list}",${i}" 
    done

    mongo_pid_list=${mongo_pid_list#*,}
    if [ -n "${mongo_pid_list}" ]; then
        echo "top -b -p ${mongo_pid_list} >> ${output_dir}/mongodb_pid/mongodb.cpu & "
        top -b -p ${mongo_pid_list} >> ${output_dir}/mongodb_pid/mongodb_${cmd}.cpu & 
    fi
fi
