#! /bin/bash

(time /opt/app/ycsb-mongodb-binding-0.15.0/bin/ycsb $2 mongodb-async -s -threads 100 -p status.interval=5 -P ./workload/load -p mongodb-async.dir=/opt/data/css/mongodb-4.0.10 >> ${1} 2>&1 & ); (time /opt/app/ycsb-mongodb-binding-0.15.0/bin/ycsb $2 mongodb-async -s -threads 100 -p status.interval=5 -P $3_1 -p mongodb-async.dir=/opt/data/css/mongodb-4.0.10 >> ${1}.1 2>&1 &);(time /opt/app/ycsb-mongodb-binding-0.15.0/bin/ycsb $2 mongodb-async -s -threads 100 -p status.interval=5 -P $3_2 -p mongodb-async.dir=/opt/data/css/mongodb-4.0.10 >> ${1}.2 2>&1 &);(time /opt/app/ycsb-mongodb-binding-0.15.0/bin/ycsb $2 mongodb-async -s -threads 100 -p status.interval=5 -P $3_3 -p mongodb-async.dir=/opt/data/css/mongodb-4.0.10 >> ${1}.3 2>&1 &)

