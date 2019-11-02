#!/bin/bash

cfg_file=$1
if [ "$1" = "" ]; then echo -e "Usage:\n\t2_initdb.sh cfg_file"; exit 1; fi
if [ ! -e ${cfg_file} ]; then echo "can't find configuration file [${cfg_file}]", exit 2; fi
source ${cfg_file}

./stop.sh

if [ "${mysql_datadir}" != "" ] && [ ! -e ${mysql_datadir} ];
then 
        sudo mkdir -p ${mysql_datadir};
fi
sudo chown -R `whoami`:`whoami` ${mysql_datadir};

if [ "${mysql_redologdir}" != "" ]  && [ ! -e ${mysql_redologdir} ];
then 
        sudo mkdir -p ${mysql_redologdir};
fi
sudo chown -R `whoami`:`whoami` ${mysql_redologdir};

if [ "${mysql_tmpdir}" != "" ] && [ ! -e ${mysql_tmpdir} ];
then
        sudo mkdir -p ${mysql_tmpdir};
fi
sudo chown -R `whoami`:`whoami` ${mysql_tmpdir};

if [ "${mysql_datadir}" != "" ] ; then rm -rf ${mysql_datadir}/*; fi
if [ ! -e ${mysql_basedir}/logs ]; then mkdir ${mysql_basedir}/logs; fi
if [ -e ${mysql_basedir}/logs/error.log ];
then
        mv ${mysql_basedir}/logs/error.log ${mysql_basedir}/logs/error-`date +%Y%m%d_%H%M%S`.log
fi

${mysql_basedir}/bin/mysqld \
        --defaults-file=${mysql_cnf} \
        --initialize-insecure \
        --explicit_defaults_for_timestamp=true \
        --default_authentication_plugin=mysql_native_password

mysql_pwd_bk=${mysql_pwd}
mysql_pwd=""
# after initialization the root password is not set
./start.sh ${cfg_file}
mysql_pwd=${mysql_pwd_bk}
timed_out=1
for i in {1..120};
do
        ${mysql_basedir}/bin/mysql --socket=${mysql_socket} -u${mysql_user} \
                           -e "set password for '${mysql_user}'@'localhost' = PASSWORD('${mysql_pwd}')"
        if [ $? -eq 0 ];
        then
                timed_out=0;
                break;
        else
                 echo -e "mysql service is not ready, wait for 10 seconds and retry";
                 sleep 10;
        fi
done
if [ ${timed_out} -ne 0 ]; then echo -e "\nwaiting for mysql service ready timed out!\n"; exit 1; fi

${mysql_basedir}/bin/mysql --socket=${mysql_socket} -u${mysql_user} -p${mysql_pwd} \
                           -e "GRANT ALL PRIVILEGES ON *.* TO '${mysql_user}'@'%' IDENTIFIED BY '${mysql_pwd}'"
${mysql_basedir}/bin/mysql --socket=${mysql_socket} -u${mysql_user} -p${mysql_pwd} \
                           -e "create database ${db_name}"
