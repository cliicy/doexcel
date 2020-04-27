#!/bin/bash

# $1 is the path of sys_affinity_irq.sfx_messages

sed_opt=" -r "

irq_msg=$1
qaf=irq_afty
grep -E "qid\s+[0-9]+\s+affinity\s+[0-9]+" ${irq_msg} > ${qaf}


echo "qid,affinity" > ${irq_msg}.csv

cofile=cqaf

cat ${qaf}  | grep , | awk -F ',' '{print $1"\n",$2}' > ${cofile}
cat ${qaf}  | grep \; | awk -F ';' '{print $1"\n",$2,$3}' >> ${cofile}

cat ${cofile} | sed ${sed_opt} 's/.*qid\s+([0-9]+)\s+affinity\s+([0-9]+).*/\1,\2/g' >> ${irq_msg}.csv
cat ${irq_msg}  | grep -E "CPU\s+[0-9]+\s+qid\s+[0-9]+\s+cpumask" | sed ${sed_opt} 's/.*CPU\s+([0-9]+)\s+qid\s+([0-9]+).*/\2,\1/g' >> ${irq_msg}.csv

rm ${qaf}
rm ${cofile}
