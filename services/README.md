Unit files to run several services and docker containers on GCP VM startup.

- cws.service

Start a docker container running 4 CMS Contest Web Servers and other CMS services except workers and scoreboard.

- rws.serivce

Start a docker container running CMS Ranking Web Server.

- worker.service

Start a docker container running single CMS Worker.

- nginx.service

Start a docker running unofficially built nginx server.

- proxy.service

Start a service running GCP SQL proxy.
