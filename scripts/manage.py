#!/usr/bin/env python3
import os
import subprocess
import sys
import re
from threading import Thread
from config import config
from create_user_data import gen_user_data

"""
This command line script helps managing CMS containers on GCP.
"""

os.chdir(os.path.dirname(sys.path[0]))

def create_main():
    print("[*] Creating Main CMS Instance")
    subprocess.run([
      "gcloud", "beta", "compute", "instances", "create", "main",
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "--machine-type", "n1-standard-4",
      "--scopes", "https://www.googleapis.com/auth/sqlservice.admin",
      "--image-family", "coreos-stable",
      "--image-project", "coreos-cloud",
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
      "--image-family", "coreos-stable",
      "--image-project", "coreos-cloud",
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
        return (False, ""), []
    lines = lines.split('\n')[1:]
    main = (False, "")
    worker = []
    for l in lines:
        nm = l.split()[0]
        if nm == "main":
            main = (True, l.split()[4])
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

def print_usage():
    print("""
Usage: manage.py <start|stop|scale|query> [args]

This command line script helps managing CMS containers on GCP.

start:
    Start main cms services. (All services except workers)

stop:
    Stop and delete main cms services. (All services except workers)
    
    if flag -a given, then all services including workers will be stoped.

scale:
    Scale the number of workers to the given target.

    Need exactly one non-negative integer as argument.

    Note: The given number should not exceed MAX_NUM_OF_WORKERS variable specified in config.yaml

query:
    Get status of current running instances.

    Use this command to get public IP of the main instance.""")


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 0:
        print_usage()
        exit(0)
    if args[0] == 'start':
        main_stat, cur_workers = query()
        if main_stat[0]:
            print("[!] Sorry, Main CMS instance is already running")
            exit(1)
        gen_user_data()
        create_main()
    elif args[0] == 'stop':
        main_stat, cur_workers = query()
        if len(args) == 2 and args[1] == '-a':
            thds = []
            for i in cur_workers:
                thds.append(run_thd(delete_worker,i))
            if main_stat[0]:
                thds.append(run_thd(delete_main))
            for thd in thds:
                thd.join()
        else:
            if not main_stat[0]:
                print("[!] Sorry, Main CMS instance is not running.")
                exit(1)
            delete_main()
    elif args[0] == 'scale':
        if len(args) == 1:
            print("[!] Scale command takes exactly one argument - target worker count")
            exit(1)
        num = int(args[1])
        if num > config.MAX_NUM_OF_WORKER:
            print("[!] Sorry, target number should not exceed MAX_NUM_OF_WORKER setting in config.yaml, which is currently {}".format(config.MAX_NUM_OF_WORKER))
            exit(1)
        scale_worker(num)
    elif args[0] == 'query':
        main_stat, cur_workers = query()
        if main_stat[0]:
            print("Main CMS instance is running. IP: {}".format(main_stat[1]))
        else:
            print("Main CMS instance is NOT running.")
        print("There are {} running worker(s):".format(len(cur_workers)))
        if len(cur_workers):
            print("[*] " + ", ".join(list(map(str, cur_workers))))
    else:
        print("[!] Unknown command!")
        print_usage()
        exit(1)

print("[*] Done!")


