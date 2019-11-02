
function generate_fio_csv() {
    # this function is to convert Sysbench test output to CSV file,
    # and convert iostat result (CPU/IO) to CSV file.

    output_dir=$1
    pushd ${output_dir}
    fdname=${output_dir##*/}
    rd=rawdisk
    fs=fs

    if echo ${fdname}  |grep -q ${rd}; then disktype=${rd}; else disktype=${fs};fi
    jobs=`echo $fdname | sed -r 's/.*([1-9])jbs.*/\1/g'`

    if [ ! -e csv ]; then mkdir csv; fi

    latc="lat (us)"
    bwh=" write throughput MB/s"
    latv=" "
    bwv=" "
    for f in `ls *.out`;
    do
        outfile=${f##*/}
        outflag=${outfile%.out}
        #echo "oooo $outflag 0000"
	disk=`echo ${outflag} | cut -d '_' -f2`

        #if [ -z "${disk}" ]; then
	#    index=`echo ${outflag} | cut -d '_' -f1`
	#    disk=`echo ${outflag} | cut -d '_' -f2`
	#fi

        latc=${latc},${outflag}
        bwh=${bwh},${outflag}

        vv=`grep -w "lat (usec): min" $f | cut -d ',' -f3 | cut -d '=' -f2`
        bw=`grep -w "WRITE: bw" $f | cut -d '=' -f2 | cut -d ',' -f1 | awk '{print $2}' | sed -r 's/\(([0-9.]+).*/\1/g'`
        #echo $vv
        latv=${latv},${vv}
        bwv=${bwv},${bw}
    done

    csv_file=${output_dir}/csv/fio_${disk}_${jobs}job_${disktype}.csv
    echo ${latc}>${csv_file}
    echo ${latv}>>${csv_file}

    echo -e "\n\n" >>${csv_file}
    echo ${bwh}>>${csv_file}
    echo ${bwv}>>${csv_file}
    popd
}


function dofio_csv() {
    for df in `ls $1`
    do
	outd=$1"/"$df
        if [ -d ${outd} ]
        then
            #echo ${outd}
            generate_fio_csv ${outd}
        fi
    done
}

dofio_csv $1
