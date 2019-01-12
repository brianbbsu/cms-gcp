#!/usr/bin/env python3
import yaml
import json
import os
import sys
from config import config

os.chdir(os.path.dirname(sys.path[0]))

def gen_user_data():
    print("[*] Generating User Data")
    with open(os.path.join("services","nginx.service"),"r") as f:
        nginx_service = f.read()

    with open(os.path.join("services","proxy.service"),"r") as f:
        proxy_service = f.read()

    with open(os.path.join("services","cws.service"),"r") as f:
        cws_service = f.read()

    with open(os.path.join("services","rws.service"),"r") as f:
        rws_service = f.read()

    with open(os.path.join("services","worker.service"),"r") as f:
        worker_service = f.read()

    with open(os.path.join("config","cms.conf"),"r") as f:
        cms_conf = f.read()

    with open(os.path.join("config","cms.ranking.conf"),"r") as f:
        cms_ranking_conf = f.read()

    with open(os.path.join("config","cms.nginx.conf"),"r") as f:
        cms_nginx_conf = f.read()


    cms_conf_dt = json.loads(cms_conf)

    for i in range(config.MAX_NUM_OF_WORKER):
        cms_conf_dt["core_services"]["Worker"].append(
           ["worker{}.GCP_ZONE.c.GCP_PROJ.internal".format(i), 
           26000])

    cms_conf = json.dumps(cms_conf_dt,indent = 2)
    
    cms_conf = cms_conf.replace("GCP_ZONE",config.GCP_ZONE).replace("GCP_PROJ",config.GCP_PROJ)

    cws_service = cws_service.replace("[CMS_CONTEST_ID]", str(config.CMS_CONTEST_ID))

    proxy_service = proxy_service.replace("GCP_ZONE",config.GCP_ZONE).replace("GCP_PROJ",config.GCP_PROJ)

    cws_service = cws_service.replace("[CMS_DOCKER_IMAGE]", config.CMS_DOCKER_IMAGE)
    rws_service = rws_service.replace("[CMS_DOCKER_IMAGE]", config.CMS_DOCKER_IMAGE)
    worker_service = worker_service.replace("[CMS_DOCKER_IMAGE]", config.CMS_DOCKER_IMAGE)

    main_user_data = {
      "coreos" : {
          "units" : [{
            "name" : "nginx.service",
            "enable" : True,
            "command" : "start",
            "content" : nginx_service            
          },{
            "name" : "cws.service",
            "enable" : True,
            "command" : "start",
            "content" : cws_service            
          },{
            "name" : "rws.service",
            "enable" : True,
            "command" : "start",
            "content" : rws_service            
          },{
            "name" : "proxy.service",
            "enable" : True,
            "command" : "start",
            "content" : proxy_service            
          }
        ]
      },
      "write_files" : [{
          "path" : "/home/core/cms-data/cms.conf",
          "permission" : "0666",
          "owner" : "root",
          "content" : cms_conf
        },{
          "path" : "/home/core/cms-data/cms.nginx.conf",
          "permission" : "0666",
          "owner" : "root",
          "content" : cms_nginx_conf
        },{
          "path" : "/home/core/cms-data/cms.ranking.conf",
          "permission" : "0666",
          "owner" : "root",
          "content" : cms_ranking_conf
        }

      ]
    }

    worker_user_data = {
      "coreos" : {
          "units" : [{
            "name" : "worker.service",
            "enable" : True,
            "command" : "start",
            "content" : worker_service            
          },{
            "name" : "proxy.service",
            "enable" : True,
            "command" : "start",
            "content" : proxy_service            
          }
        ]
      },
      "write_files" : [{
          "path" : "/home/core/cms-data/cms.conf",
          "permission" : "0666",
          "owner" : "root",
          "content" : cms_conf
        }]
    }


    with open(os.path.join("user-data","main.yaml"),"w") as f:
        f.write("#cloud-config\n\n")
        f.write(yaml.dump(main_user_data))

    with open(os.path.join("user-data","worker.yaml"),"w") as f:
        f.write("#cloud-config\n\n")
        f.write(yaml.dump(worker_user_data))

if __name__ == "__main__":
    gen_user_data()
