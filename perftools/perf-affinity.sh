#!/bin/bash

qaf=qaffinity
grep -E "qid\s+[0-9]+\s+affinity\s+[0-9]+" sfx_messages > ${qaf}


echo "qid,affinity" > ${qaf}.csv

cofile=cqaf

cat ${qaf}  | grep , | awk -F ',' '{print $1"\n",$2}' > ${cofile}
cat ${qaf}  | grep \; | awk -F ';' '{print $1"\n",$2,$3}' >> ${cofile}

cat ${cofile} | sed -r 's/.*qid\s+([0-9]+)\s+affinity\s+([0-9]+).*/\1,\2/g' >> ${qaf}.csv