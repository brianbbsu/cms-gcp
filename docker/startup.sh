#!/bin/bash

wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /cloud_sql_proxy
chmod +x /cloud_sql_proxy
/cloud_sql_proxy -instances=cms-server-211312:asia-east1:cmsdb=tcp:5432 --quiet &

if [[ ! -v CMS_INSTANCE_TYPE ]]; then
    echo "CMS_INSTANCE_TYPE not SET!!!"
    exit 1
fi

if [ $CMS_INSTANCE_TYPE = "MAIN" ]; then
    if [[ ! -v CMS_CONTEST_ID ]]; then
        echo "CMS_CONTEST_ID not set!!!"
        exit 1
    fi
    cmsResourceService 0 -a $CMS_CONTEST_ID &
    cmsLogService 0
elif [ $CMS_INSTANCE_TYPE = "WORKER" ]; then
    cmsWorker
else
    echo "Unknown instance type"
    exit 1
fi 
