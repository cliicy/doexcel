#!/bin/bash

function show_case_detail() {
    echo "mysql_cnf             =${mysql_cnf}"
    echo "sysbench_cnf          =${sysbench_cfg}"
    echo "create_tbl_opt        =${create_tbl_opt}"
    echo "table_data_src_file   =${table_data_src_file}"
    echo "case_id               =${case_id}"
    echo "output_dir            =${output_dir}"
    echo -e "\n"
}

if [ "$1" == "formal" ];
then
    cmpr_list=("none")
    cup_list=("perf")
    aw_list=("off")
    avl_ratio_list=("normal")
    sb_large=./sysbench-cfg/benchmark.cfg
    sb_small=./sysbench-cfg/benchmark.cfg
    # run_workloads="prepare"
    run_workloads="prepare oltp_update_index oltp_update_non_index oltp_read_write oltp_write_only oltp_read_only"
else
    cmpr_list=("none")
    cup_list=("perf")
    aw_list=("off")
    avl_ratio_list=("normal")
    sb_large=./sysbench-cfg/benchmark.cfg
    sb_small=./sysbench-cfg/benchmark.cfg
    run_workloads="oltp_update_index oltp_update_non_index"
fi

cpu_cores=`lscpu | grep "^CPU(s):" | sed -r 's/\s+/,/g' | cut -d , -f 2`

for cmpr in ${cmpr_list[@]};
do
#    if [ "${cmpr}" == "none" ];
#    then
#        ratio_list=("N/A")
#    else
        ratio_list=${avl_ratio_list[@]}
#    fi

    for ratio in ${ratio_list[@]};
    do
        for aw in ${aw_list[@]};
        do
            for cup in ${cup_list[@]};
            do
                my_cnf=./mysql-cnf/${cup}-aw-${aw}.cnf
                sysbench_cfg=${sb_large}
                if [ "${cup}" == "tall" ]; then sysbench_cfg=${sb_small}; fi
                source ${sysbench_cfg}

                export mysql_cnf=${my_cnf}

                if [ "${ratio}" == "N/A" ];
                then
                    export create_tbl_opt=
                    export table_data_src_file="../compress/${ratio}.txt"
                    export case_id=-${cmpr}-aw-${aw}-${cup}
                else
                    export create_tbl_opt="compression='${cmpr}'"
                    export table_data_src_file="../compress/${ratio}.txt"
                    export case_id=-${cmpr}-${ratio}-aw-${aw}-${cup}
                fi
                export output_dir=${result_dir}sb-`date +%Y%m%d_%H%M%S`${case_id}
                show_case_detail
                if [ ! -e ${output_dir} ]; then mkdir -p ${output_dir}; fi
                cp ${sysbench_cfg} ${output_dir}
                cp ${mysql_cnf} ${output_dir}
                #
                # actual variable already sourced in above
                # global environment variables are used to pass them around
                # here an empty dummy cfg file is dirty hack used to
                # pass parameter check
                #
#                ./1_prep_dev.sh ./sysbench-cfg/dummy.cfg
#                ./2_initdb.sh   ./sysbench-cfg/dummy.cfg
                export threads=$((${cpu_cores}*2))
                export workload_set=${run_workloads}
                ./3_run.sh      ./sysbench-cfg/dummy.cfg
            done
        done
    done
done

