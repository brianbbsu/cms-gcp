#! /bin/bash
set -e

#install Stackdriver Monitoring agent
curl -sSO https://dl.google.com/cloudagents/install-monitoring-agent.sh
sudo bash install-monitoring-agent.sh

#install Stackdriver Logging agent
curl -sSO https://dl.google.com/cloudagents/install-logging-agent.sh
sudo bash install-logging-agent.sh --structured

#Setup config files and directories
mkdir -p /cms/

cat <<EOF > /cms/cms.conf
[CMS_CONFIG]
EOF

#install docker
curl -fsSL https://get.docker.com | sh

#pull image of Google Cloud SQL proxy
docker pull gcr.io/cloudsql-docker/gce-proxy:1.12

#start Google Cloud SQL proxy in a container
docker run -d --rm --name proxy -p 127.0.0.1:5432:5432 gcr.io/cloudsql-docker/gce-proxy:1.12 /cloud_sql_proxy -instances=[GCP_PROJ]:[GCP_ZONE]:cmsdb=tcp:0.0.0.0:5432

#pull image of Contest Management System
docker pull [CMS_DOCKER_IMAGE]

#start cms worker in a container
docker run --name worker -d -t -v /cms/cms.conf:/usr/local/etc/cms.conf:ro --privileged --network=host -e CMS_INSTANCE_TYPE=WORKER [CMS_DOCKER_IMAGE]

