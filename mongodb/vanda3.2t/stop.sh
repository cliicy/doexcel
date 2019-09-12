#!/bin/bash

kill -9 `ps aux | grep -v grep | grep -e bin/mongod | cut -c 10-15`

for i in {1..100};
do
    ps aux | grep -v grep | grep -e bin/mongod
    if [ $? -ne 0 ]; then echo stopped; sleep 10; break; fi
    echo "waiting for mongodb to exit"
    sleep 3
done
