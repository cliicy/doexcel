#! /bin/bash

cfg_file=$1
if [ "${cfg_file}" = "" ]; then echo -e "Usage:\n\t3_run.sh cfg_file"; exit 1; fi
if [ ! -e ${cfg_file} ]; then echo "can't find configuration file [${cfg_file}]", exit 2; fi
source ${cfg_file}

# output_dir will be used in fio.sh, so make it global
if [ "${output_dir}" == "" ];
then
        export output_dir=${result_dir}/${logfolder}-`date +%Y%m%d_%H%M%S`${case_id}
fi

echo "test output will be saved in ${output_dir}"
if [ ! -e ${output_dir} ]; then mkdir -p ${output_dir}; fi

# collect MySQL startup options / configuration / test script
cp $0 ${output_dir}
cp ${cfg_file} ${output_dir}
cp ${app_pgconf%/*}/postgresql.conf ${output_dir}

source ../lib/common-lib
source ../lib/bench-lib

collect_sys_info ${output_dir} ${css_status}

echo "export output_dir=${output_dir}" > ./output.dir
#collect some extra information
pginfo=${output_dir}/postgresql.opts
cmd_psql=${app_basedir}/bin/psql
${cmd_psql} -c 'show shared_buffers' postgres > ${pginfo} 
${cmd_psql} -c 'show wal_compression' postgres >> ${pginfo} 
${cmd_psql} -c 'show max_wal_size' postgres >> ${pginfo} 
ps aux | grep postgresql | grep -v grep >> ${pginfo}

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
        tail -f -n 0 ${app_dbglog} > ${output_dir}/${workload_fname}.${app}.log &
        echo $! > ${output_dir}/tail.${workload_fname}.${app}.log.pid
        # try to keep existing result file
        if [ -e ${output_dir}/${workload_fname}.result ];
        then
                mv ${output_dir}/${workload_fname}.result ${output_dir}/${workload_fname}-`date +%Y%m%d_%H%M%S`.result
        fi
        echo "${workload_fname} starts at: " `date +%Y-%m-%d\ %H:%M:%S` > ${output_dir}/${workload_fname}.result

        iostat -txdmc ${rpt_interval} ${disk} >> ${output_dir}/${workload_fname}.iostat &
        echo $! > ${output_dir}/${workload_fname}.iostat.pid

	#cp ./workload/${workload} ${output_dir}
	# run postgreSQL workload, all parameters are from case-cfg/cfg_file
        #if [ "${cmd}" == "load" ]; then
        #    cmdline="time ${app_basedir}/bin/pgbench -i -s ${scale} -F ${fillfact} -U ${user} -h ${host} -n -q -d ${dbname}"
        #    #cmdline="time ${app_basedir}/bin/pgbench -i --unlogged-tables -s ${scale} -F ${fillfact} -U ${user} -h ${host} -n -q -d ${dbname}"
        #else
        #    cmdline="time ${app_basedir}/bin/pgbench -r -j ${jobs} -c ${clients} -P ${rpt_interval} -T ${run_time} -U ${user} -h ${host} ${dbname} \ 
        #             -f ./workloads/vandat.sql"
        #fi
	
        #echo ${cmdline} >> ${pginfo}
        #if [ "${cmd}" == "load" ]; then
        #    time ${cmdline} >> ${output_dir}/${workload_fname}.result 2>&1  
        #else
        #    time ${cmdline} >> ${output_dir}/${workload_fname}.result   
        #fi
        time sysbench \
                --db-driver=pgsql --pgsql-db=${dbname} --pgsql-user=${user} \
                --report-interval=${rpt_interval} --time=${run_time} --threads=${threads} \
                --percentile=${percentile} ${sysbench_dir}/${workload}.lua\
                --warmup-time=${warmup_time} --rand-type=${rand_type} --histogram=on \
                --tables=${table_count} --table-size=${table_size} \
                --create-table-options=${create_tbl_opt} \
                --table-data-src-file=${table_data_src_file} \
                ${cmd} \
                >> ${output_dir}/${workload_fname}.result

        ps aux | grep sysbench | grep -v grep >> ${pginfo}

        du --block-size=1G ${app_datadir} > ${output_dir}/${workload_fname}.dbsize
        cat /sys/block/${dev_name}/sfx_smart_features/sfx_capacity_stat >> ${output_dir}/${workload_fname}.dbsize

        echo -e "\nsfx_messages ends at: `date +%Y-%m-%d_%H:%M:%S`\n"  >> ${output_dir}/${workload_fname}.sfx_message
        echo ${output_dir}/tail.${workload_fname}.pid
        kill `cat ${output_dir}/tail.${workload_fname}.pid`
        rm -f ${output_dir}/tail.${workload_fname}.pid
        echo -e "\niostat ends at: " `date +%Y-%m-%d_%H:%M:%S` >> ${output_dir}/${workload_fname}.iostat
        echo -e "\n${workload_fname}" "\nends at: " "`date +%Y-%m-%d_%H:%M:%S`" >> ${output_dir}/${workload_fname}.result
        echo ${output_dir}/${workload_fname}.iostat.pid
        kill `cat ${output_dir}/${workload_fname}.iostat.pid`
        rm -f ${output_dir}/${workload_fname}.iostat.pid
        kill `cat ${output_dir}/tail.${workload_fname}.${app}.log.pid`
        rm -f ${output_dir}/tail.${workload_fname}.${app}.log.pid
        # sleep ${sleep_after_case}
        sleep 60
        echo -e "select pg_database_size('${dbname}')/1024/1024/1024||'G'
" | ${cmd_psql} ${dbname} > ${output_dir}/${workload_fname}.pgdbsz
        echo -e "select pg_indexes_size('${tbname}')/1024/1024/1024||'G'
" | ${cmd_psql} ${dbname} > ${output_dir}/${workload_fname}.pgindexsz
    done

generate_csv ${output_dir}
get_dbsize_new ${output_dir}

ssd_name=$(basename "$PWD")
#ffactor=`echo -e "\d+ pg_trigger" | ${cmd_psql} ${dbname} | grep fillfactor | cut -d ':' -f2 | cut -d '=' -f2`
#ffactor=`echo -e "\d+ pgbench_accounts" | ${cmd_psql} ${dbname} | grep fillfactor | cut -d ':' -f2 | cut -d '=' -f2`
#gen_benchinfo_postgres ${ssd_name} ${scale} ${output_dir} ${ffactor}
gen_benchinfo_postgres ${ssd_name} ${table_count}.${table_size} ${output_dir} 

