
function generate_fio_csv() {
    # this function is to convert Sysbench test output to CSV file,
    # and convert iostat result (CPU/IO) to CSV file.
    output_dir=$1
    pushd ${output_dir}
    if [ ! -e csv ]; then mkdir csv; fi

    latc="lat (us)"
    bwh=" write throughput MB/s"
    latv=" "
    bwv=" "
    for f in `ls *.out`;
    do
        outfile=${f##*/}
        outflag=${outfile%.out}

        if [ -z "${disk}" ]; then
	    disk=`echo ${outflag} | cut -d '_' -f1`
	fi

        latc=${latc},${outflag}
        bwh=${bwh},${outflag}

        vv=`grep -w "lat (usec): min" $f | cut -d ',' -f3 | cut -d '=' -f2`
        bw=`grep -w "WRITE: bw" $f | cut -d '=' -f2 | cut -d ',' -f1 | awk '{print $2}' | sed -r 's/\(([0-9.]+).*/\1/g'`
        #echo $vv
        latv=${latv},${vv}
        bwv=${bwv},${bw}
    done

    csv_file=${output_dir}/csv/fio_${disk}.csv
    echo ${latc}>${csv_file}
    echo ${latv}>>${csv_file}

    echo -e "\n\n" >>${csv_file}
    echo ${bwh}>>${csv_file}
    echo ${bwv}>>${csv_file}
}





generate_fio_csv $1
