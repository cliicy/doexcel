#! /bin/bash

cfg_file=$1
if [ "${cfg_file}" = "" ]; then echo -e "Usage:\n\t3_run.sh cfg_file"; exit 1; fi
if [ ! -e ${cfg_file} ]; then echo "can't find configuration file [${cfg_file}]", exit 2; fi
source ${cfg_file}

# output_dir will be used in fio.sh, so make it global
if [ "${output_dir}" == "" ];
then
        export output_dir=${result_dir}/sb-`date +%Y%m%d_%H%M%S`${case_id}
fi

echo "test output will be saved in ${output_dir}"

if [ ! -e ${output_dir} ]; then mkdir -p ${output_dir}; fi

# collect MySQL startup options / configuration / test script
cp $0 ${output_dir}
cp ${cfg_file} ${output_dir}
cp ${mysql_cnf} ${output_dir};
ps aux | grep mysqld | grep -v grep > ${output_dir}/mysqld.cmdline

source ../lib/common-lib
collect_sys_info ${output_dir} ${css_status}

echo "will run workload(s) ${workload_set}"
for workload in ${workload_set};
    do
        echo "run workload ${workload}"
	cmd="run"
        # workload friendly name. it will be used in fio.sh, so make it global
        export workload_fname=${workload}
	if [ "prepare" == "${workload}" ]; then cmd="prepare"; workload="oltp_common"; workload_fname="prepare"; fi
        echo -e "sfx_message starts at: " `date +%Y-%m-%d\ %H:%M:%S` "\n"  > ${output_dir}/${workload_fname}.sfx_message
        sudo chmod 666 /var/log/sfx_messages;
	tail -f -n 0 /var/log/sfx_messages >> ${output_dir}/${workload_fname}.sfx_message &
        echo $! > ${output_dir}/tail.${workload_fname}.pid
        echo "iostat start at: " `date +%Y-%m-%d\ %H:%M:%S` > ${output_dir}/${workload_fname}.iostat
        # try to keep existing result file
        if [ -e ${output_dir}/${workload_fname}.result ];
        then
                mv ${output_dir}/${workload_fname}.result ${output_dir}/${workload_fname}-`date +%Y%m%d_%H%M%S`.result
        fi
        echo "${workload_fname} starts at: " `date +%Y-%m-%d\ %H:%M:%S` > ${output_dir}/${workload_fname}.result

        iostat -txdmc ${rpt_interval} ${disk}* >> ${output_dir}/${workload_fname}.iostat &
        echo $! > ${output_dir}/${workload_fname}.iostat.pid
        # clearn data in MySQL performance schema tables
        truncate_sys_tables 

        start_collect_mysql_lat_act ${output_dir} $((${run_time}+${warmup_time})) ${workload_fname} &

        # run sysbench workload, all parameters are from sysbench.cfg
        time sysbench \
                --db-driver=mysql  --mysql-socket=${mysql_socket} \
                --mysql-db=${db_name} --mysql-user=${mysql_user} --mysql-password=${mysql_pwd} \
                --report-interval=${rpt_interval} --time=${run_time} --threads=${threads} \
                --percentile=${percentile} ${sysbench_dir}/${workload}.lua\
                --warmup-time=${warmup_time} --rand-type=${rand_type} --histogram=on \
                --tables=${table_count} --table-size=${table_size} \
                --create-table-options=${create_tbl_opt} \
                --table-data-src-file=${table_data_src_file} \
                ${cmd} \
                >> ${output_dir}/${workload_fname}.result
       
        stop_collect_mysql_lat_act ${output_dir}
        
        du --block-size=1G ${mysql_datadir} > ${output_dir}/${workload_fname}.dbsize
        df -h ${disk} >> ${output_dir}/${workload_fname}.dbsize
        cat /sys/block/${dev_name}/sfx_smart_features/sfx_capacity_stat >> ${output_dir}/${workload_fname}.dbsize

        # collect redo log perf counter data
        collect_perf_counter_redolog  ${output_dir}/${workload_fname}_redolog.counter

        echo -e "\nsfx_messages ends at: `date +%Y-%m-%d_%H:%M:%S`\n"  >> ${output_dir}/${workload_fname}.sfx_message
        echo ${output_dir}/tail.${workload_fname}.pid
        kill `cat ${output_dir}/tail.${workload_fname}.pid`
        rm -f ${output_dir}/tail.${workload_fname}.pid
        echo -e "\niostat ends at: " `date +%Y-%m-%d_%H:%M:%S` >> ${output_dir}/${workload_fname}.iostat
        echo -e "\n${workload_fname}" "\nends at: " "`date +%Y-%m-%d_%H:%M:%S`" >> ${output_dir}/${workload_fname}.result
        echo ${output_dir}/${workload_fname}.iostat.pid
        kill `cat ${output_dir}/${workload_fname}.iostat.pid`
        rm -f ${output_dir}/${workload_fname}.iostat.pid
        sleep 10
    done

generate_csv ${output_dir}
