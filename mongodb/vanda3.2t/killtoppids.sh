ps -ef | grep top | awk '{print $2}'> toppid
for i in `cat toppid`; do kill -9  $i; done
