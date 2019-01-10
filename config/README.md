Config files for this system to work.

- config.yaml

Settings related to google cloud platform and infrastructure.
Ex: GCP project id, GCP instance type, number of workers, CMS contest id...

- cms.conf

CMS main config. Variable like GCP\_ZONE and GCP\_PROJ will be replaced automatically by the system when transfering to the server.

Worker field in "core\_services" section are intentionally blanked. It will be filled out by the system according to settings in config.yaml.

Remember to change the secret\_key every time you hold a new contest.

For more information about cms.conf, see https://cms.readthedocs.io/en/v1.4/Running%20CMS.html.

- cms.ranking.conf

CMS scoreboard config. Remember to change username and password to something else.

For more information about cms.ranking.conf, see https://cms.readthedocs.io/en/v1.4/RankingWebServer.html.

- cms.nginx.conf

Nginx config for CMS Main Instance.

We use an unofficially built docker with built in sticky session support for load balancing.
