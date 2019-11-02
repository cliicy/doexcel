sudo su -c "echo 5242880 > /proc/sys/vm/min_free_kbytes"
sudo su -c "echo 2 > /proc/sys/vm/dirty_writeback_centisecs"
sudo su -c "echo 2 > /proc/sys/vm/dirty_expire_centisecs"
