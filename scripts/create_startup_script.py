#!/usr/bin/env python3
import yaml
import json
import os
import sys
from config import config

os.chdir(os.path.dirname(sys.path[0]))

def create_startup_script():
    print("[*] Generating User Data")

    with open(os.path.join("config","cms.conf"),"r") as f:
        cms_conf = f.read()

    with open(os.path.join("config","cms.ranking.conf"),"r") as f:
        cms_ranking_conf = f.read()

    with open(os.path.join("config","cms.nginx.conf"),"r") as f:
        cms_nginx_conf = f.read()

    with open(os.path.join("startup","main.sh"),"r") as f:
        main_sh = f.read()

    with open(os.path.join("startup","worker.sh"),"r") as f:
        worker_sh = f.read()

    cms_conf_dt = json.loads(cms_conf)

    for i in range(config.MAX_NUM_OF_WORKER):
        cms_conf_dt["core_services"]["Worker"].append(["worker{}.[GCP_ZONE].c.[GCP_PROJ].internal".format(i), 26000])

    cms_conf = json.dumps(cms_conf_dt,indent = 2)
    
    main_sh = main_sh.replace("[CMS_CONFIG]", cms_conf)
    main_sh = main_sh.replace("[CMS_RANKING_CONFIG]", cms_ranking_conf)
    main_sh = main_sh.replace("[CMS_NGINX_CONFIG]", cms_nginx_conf)

    main_sh = main_sh.replace("[CMS_CONTEST_ID]", str(config.CMS_CONTEST_ID))
    main_sh = main_sh.replace("[GCP_ZONE]",config.GCP_ZONE).replace("[GCP_PROJ]",config.GCP_PROJ)
    main_sh = main_sh.replace("[CMS_DOCKER_IMAGE]", config.CMS_DOCKER_IMAGE)


    worker_sh = worker_sh.replace("[CMS_CONFIG]", cms_conf)

    worker_sh = worker_sh.replace("[CMS_CONTEST_ID]", str(config.CMS_CONTEST_ID))
    worker_sh = worker_sh.replace("[GCP_ZONE]",config.GCP_ZONE).replace("[GCP_PROJ]",config.GCP_PROJ)
    worker_sh = worker_sh.replace("[CMS_DOCKER_IMAGE]", config.CMS_DOCKER_IMAGE)

    with open(os.path.join("startup", ".main.sh"), "w") as f:
        f.write(main_sh)

    with open(os.path.join("startup", ".worker.sh"), "w") as f:
        f.write(worker_sh)


if __name__ == "__main__":
    create_startup_script()
