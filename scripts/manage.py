#!/usr/bin/env python3
import os
import subprocess
import sys
import re
from threading import Thread
from config import config
from gen_conf import gen_user_data

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.dirname(dname))

def create_main():
    print("[*] Creating Main CMS Instance")
    subprocess.run([
      "gcloud", "beta", "compute", "instances", "create", "main",
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "--machine-type", "n1-standard-4",
      "--scopes", "https://www.googleapis.com/auth/sqlservice.admin",
      "--image", "coreos-stable-1911-3-0-v20181106",
      "--image-project", "coreos-cloud",
      "--subnet", "main",
      "--tags", "http-server",
      "--metadata-from-file", "user-data=" + os.path.join("user-data","main.yaml")
    ], stdout = subprocess.DEVNULL)
    print("[*] Created Main CMS Instance")

def create_worker(shard):
    print("[*] Creating CMS Worker{} Instance".format(shard))
    subprocess.run([
      "gcloud", "beta", "compute", "instances", "create", "worker{}".format(shard),
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "--machine-type", "n1-standard-1",
      "--scopes", "https://www.googleapis.com/auth/sqlservice.admin",
      "--image", "coreos-stable-1911-3-0-v20181106",
      "--image-project", "coreos-cloud",
      "--subnet", "worker",
      "--metadata-from-file", "user-data=" + os.path.join("user-data","worker.yaml")
    ], stdout = subprocess.DEVNULL)
    print("[*] Created CMS Worker{} Instance".format(shard))

def delete_main():
    print("[*] Deleting Main CMS Instance")
    subprocess.run([
      "gcloud", "beta", "compute", "instances", "delete", "main",
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "-q"
    ], stdout = subprocess.DEVNULL)
    print("[*] Deleted Main CMS Instance")
    
def delete_worker(shard):
    print("[*] Deleting CMS Worker{} Instance".format(shard))
    subprocess.run([
      "gcloud", "beta", "compute", "instances", "delete", "worker{}".format(shard),
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "-q"
    ], stdout = subprocess.DEVNULL)
    print("[*] Deleted CMS Worker{} Instance".format(shard))
    
def query():
    print("[*] Querying current running instances")
    proc = subprocess.run([
      "gcloud", "beta", "compute", "instances", "list",
      "--project", config.GCP_PROJ,
      "--filter", "zone: " + config.GCP_ZONE,
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = proc.stdout.decode("utf-8").strip()
    if lines == "":
        return False, []
    lines = lines.split('\n')[1:]
    main = False
    worker = []
    for l in lines:
        nm = l.split()[0]
        if nm == "main":
            main = True
        elif re.match(r"^worker(\d+)$",nm):
            shard = int(re.match(r"^worker(\d+)$",nm).group(1))
            worker.append(shard)

    return main, worker

def run_thd(fn, *args, **kwargs):
    thd = Thread(target = fn, args = args, kwargs = kwargs)
    thd.start()
    return thd

def scale_worker(target):
    print("[*] Scaling CMS to {} worker(s)".format(target))
    main_stat, cur_workers = query()
    thds = []
    for i in cur_workers:
        if i >= target:
            thds.append(run_thd(delete_worker,i))
    
    for i in range(target):
        if i not in cur_workers:
            thds.append(run_thd(create_worker,i))

    for thd in thds:
        thd.join()

    print("[*] Scaled CMS to {} worker(s)".format(target))

if __name__ == '__main__':
    args = sys.argv[1:]
    if args[0] == 'start':
        gen_user_data()
        create_main()
    elif args[0] == 'delete':
        main_stat, cur_workers = query()
        if args[1] == 'main':
            if not main_stat:
                print("[!] Sorry, Main CMS instance is not running.")
                exit(1)
            delete_main()
        elif args[1] == 'all':
            thds = []
            for i in cur_workers:
                thds.append(run_thd(delete_worker,i))
            if main_stat:
                thds.append(run_thd(delete_main))
            for thd in thds:
                thd.join()
    elif args[0] == 'scale':
        num = int(args[1])
        if num > config.MAX_NUM_OF_WORKER:
            print("[!] Sorry, target number should not exceed MAX_NUM_OF_WORKER setting in config.yaml, which is currently {}".format(config.MAX_NUM_OF_WORKER))
            exit(1)
        scale_worker(num)
    elif args[0] == 'query':
        main_stat, cur_workers = query()
        print("Main CMS instance is {}running.".format("" if main_stat else "NOT "))
        print("There are {} running worker(s):".format(len(cur_workers)))
        if len(cur_workers):
            print("[*] " + ", ".join(list(map(str, cur_workers))))

print("[*] Done!")


