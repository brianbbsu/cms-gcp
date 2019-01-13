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
mkdir -p /cms/ranking/

cat <<EOF > /cms/cms.conf
[CMS_CONFIG]
EOF

cat <<EOF > /cms/cms.ranking.conf
[CMS_RANKING_CONFIG]
EOF

cat <<EOF > /cms/cms.nginx.conf
[CMS_NGINX_CONFIG]
EOF

#install docker
curl -fsSL https://get.docker.com | sh

#pull image of Google Cloud SQL proxy
docker pull gcr.io/cloudsql-docker/gce-proxy:1.12

#pull image of custom build nginx server (with sticky session) 
docker pull brianbbsu/nginx

#start nginx in a container
docker run -d --rm --name nginx -v /cms/cms.nginx.conf:/etc/nginx/nginx.conf:ro --network=host brianbbsu/nginx

#restart Stackdriver with nginx plugin
cat <<EOF > /opt/stackdriver/collectd/etc/collectd.d/nginx.conf
LoadPlugin nginx
<Plugin "nginx">
    URL "http://localhost:81/nginx-status"
</Plugin>
EOF
service stackdriver-agent restart

#start Google Cloud SQL proxy in a container
docker run -d --rm --name proxy -p 127.0.0.1:5432:5432 gcr.io/cloudsql-docker/gce-proxy:1.12 /cloud_sql_proxy -instances=[GCP_PROJ]:[GCP_ZONE]:cmsdb=tcp:0.0.0.0:5432

#pull image of Contest Management System
docker pull [CMS_DOCKER_IMAGE]

#start cms in a container
docker run -d -t --rm --name cws -v /cms/cms.conf:/usr/local/etc/cms.conf:ro --network=host -e CMS_INSTANCE_TYPE=MAIN -e CMS_CONTEST_ID=[CMS_CONTEST_ID] [CMS_DOCKER_IMAGE]

#start cms ranking web server in another container
docker run -d -t --rm --name rws -v /cms/cms.ranking.conf:/usr/local/etc/cms.ranking.conf:ro -v /cms/ranking:/var/local/lib/cms/ranking --network=host -e CMS_INSTANCE_TYPE=RANKING [CMS_DOCKER_IMAGE]
