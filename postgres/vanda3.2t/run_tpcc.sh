#! /bin/bash

cfg_file=$1
if [ "${cfg_file}" = "" ]; then echo -e "Usage:\n\t3_run.sh cfg_file"; exit 1; fi
if [ ! -e ${cfg_file} ]; then echo "can't find configuration file [${cfg_file}]", exit 2; fi
source ${cfg_file}

# output_dir will be used in fio.sh, so make it global
if [ "${output_dir}" == "" ];
then
        export output_dir=${result_dir}/${logfolder}-`date +%Y%m%d_%H%M%S`${case_id}.tpcc
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

echo "will run workload(s) ${tpcc_workload_set}"
lastwl=`echo ${tpcc_workload_set} | awk '{print $NF}'`
for workload in ${tpcc_workload_set};
    do
        echo "run workload ${workload}"
	cmd=${workload}
        # workload friendly name. it will be used in fio.sh, so make it global
        export workload_fname=${workload}
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

        if [ "${cmd}" == "run" ];
        then
                start_blk_trace ${output_dir} ${workload_fname} ${disk} 120 &
                ps -ef | grep blktrace | grep -v grep | awk '{print $2}' | xargs kill -15
        fi
        pushd ${sysbench_tpcc_dir}
        time ./tpcc.lua \
                --db-driver=pgsql --pgsql-db=${dbname} --pgsql-user=${user} \
                --report-interval=${rpt_interval} --time=${run_time} --threads=${threads} \
                --percentile=${percentile} \
                --warmup-time=${warmup_time} --rand-type=${rand_type} --histogram=on \
                --tables=${tpcc_table_count} --scale=${tpcc_scale_size} \
                --trx_level=RC --db-ps-mode=auto --use_fk=0 --enable_purge=yes \
                ${cmd} \
                >> ${output_dir}/${workload_fname}.result
        popd
        ps aux | grep tpcc.lua | grep -v grep >> ${pginfo}

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
        sleep ${sleep_after_case}

        # manaully run vacuum to clean up the garbages start
        #if [ "${workload_fname}" == "prepare" ] || [ "${workload_fname}" != "${lastwl}" ]; then
        if [ "${workload_fname}" == "prepare" ]; then
            echo -e "\nvacumme  starts at: `date +%Y-%m-%d_%H:%M:%S`\n"  > ${output_dir}/${workload_fname}.vacuum
            echo -e "select * from pg_stat_user_tables where relname = '${tpcc_tbname}';" | ${cmd_psql} ${dbname} >> ${output_dir}/${workload_fname}.vacuum
            echo -e "vacuum;" | ${cmd_psql} ${dbname} >> ${output_dir}/${workload_fname}.vacuum
            echo -e "select * from pg_stat_user_tables where relname = '${tpcc_tbname}';" | ${cmd_psql} ${dbname} >> ${output_dir}/${workload_fname}.vacuum
            echo -e "\nvacumme  ends at: `date +%Y-%m-%d_%H:%M:%S`\n"  >> ${output_dir}/${workload_fname}.vacuum
        fi
        # manaully run vacuum to clean up the garbages end 

        echo -e "select pg_database_size('${dbname}')/1024/1024/1024||'G'
" | ${cmd_psql} ${dbname} > ${output_dir}/${workload_fname}.pgdbsz
        echo -e "select pg_indexes_size('${tpcc_tbname}')/1024/1024/1024||'G'
" | ${cmd_psql} ${dbname} > ${output_dir}/${workload_fname}.pgindexsz
    done

generate_csv ${output_dir}
get_dbsize_new ${output_dir}

ssd_name=$(basename "$PWD")
#ffactor=`echo -e "\d+ pg_trigger" | ${cmd_psql} ${dbname} | grep fillfactor | cut -d ':' -f2 | cut -d '=' -f2`
#ffactor=`echo -e "\d+ pgbench_accounts" | ${cmd_psql} ${dbname} | grep fillfactor | cut -d ':' -f2 | cut -d '=' -f2`
#gen_benchinfo_postgres ${ssd_name} ${scale} ${output_dir} ${ffactor}
ffactor=`echo -e "\d+ ${tpcc_tbname}" | ${cmd_psql} ${dbname} | grep fillfactor | cut -d ':' -f2 | cut -d '=' -f2`
gen_benchinfo_postgres ${ssd_name} ${tpcc_table_count}.${tpcc_scale_size} ${output_dir} ${ffactor}
#echo "${ssd_name} ${table_count}.${table_size} ${output_dir} ${ffactor}" >> ${output_dir}/ben.info

