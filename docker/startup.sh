#!/bin/bash

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
elif [ $CMS_INSTANCE_TYPE = "RANKING" ]; then
    cmsRankingWebServer
else
    echo "Unknown instance type"
    exit 1
fi 
