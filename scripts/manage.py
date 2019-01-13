#!/usr/bin/env python3
import os
import subprocess
import sys
import re
from threading import Thread
from config import config
from create_startup_script import create_startup_script

"""
This command line script helps managing CMS containers on GCP.
"""

os.chdir(os.path.dirname(sys.path[0]))

def create_main():
    print("[*] Creating Main CMS Instance")
    args = [
      "gcloud", "beta", "compute", "instances", "create", "main",
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "--machine-type", config.MAIN_INSTANCE_TYPE,
      "--scopes", "https://www.googleapis.com/auth/sqlservice.admin,https://www.googleapis.com/auth/logging.admin,https://www.googleapis.com/auth/monitoring",
      "--image-family", "ubuntu-1604-lts",
      "--image-project", "ubuntu-os-cloud", 
      "--boot-disk-size", "20GB",
      "--tags", "http-server,https-server",
      "--verbosity", "error",
      "--metadata-from-file", "startup-script=" + os.path.join("startup", ".main.sh") 
    ]
    if config.MAIN_INSTANCE_IP != "":
        args += ["--address", config.MAIN_INSTANCE_IP]
    subprocess.run(args, stdout = subprocess.DEVNULL)
    main, _ = query()
    print("[*] Created Main CMS Instance IP: {}".format(main[1]))

def create_worker(shard):
    print("[*] Creating CMS Worker{} Instance".format(shard))
    subprocess.run([
      "gcloud", "beta", "compute", "instances", "create", "worker{}".format(shard),
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "--machine-type", config.WORKER_INSTANCE_TYPE,
      "--scopes", "https://www.googleapis.com/auth/sqlservice.admin,https://www.googleapis.com/auth/logging.admin,https://www.googleapis.com/auth/monitoring",
      "--image-family", "ubuntu-1604-lts",
      "--image-project", "ubuntu-os-cloud", 
      "--boot-disk-size", "20GB",
      "--verbosity", "error",
      "--metadata-from-file", "startup-script=" + os.path.join("startup", ".worker.sh")
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
      "gcloud", "beta", "compute", "ssh", "worker{}".format(shard),
      "--command", "sudo docker stop worker",
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "-q"
    ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
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

def run_on_instance(ins, cmd, pipe = False):
    print("[*] Executing \"{}\" on {}".format(cmd, ins))
    proc = subprocess.run([
      "gcloud", "beta", "compute", "ssh", ins,
      "--command", cmd,
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "-q"
    ], stdout = (subprocess.PIPE if pipe else None))
    if pipe:
        return proc.stdout.decode("utf-8").strip()

def send_ranking_data():
    print("[*] Sending ranking logo, flags, and faces to Main CMS Instance")
    file_list = []
    for root, dirs, files in os.walk("ranking"):
        for file in files:
            if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".bmp") or file.endswith(".gif"):
                 file_list.append(os.path.join(root, file))
    if not len(file_list):
        print("[!] There should be at least one image in the folder!")
        return
    proc1 = subprocess.run(
      ["tar", "-cz"] + file_list,
      stdout = subprocess.PIPE)
    sz = sys.getsizeof(proc1.stdout)
    print("[*] Sending {} file(s), size: {:.2f} KB....".format(len(file_list), sz / 8 / 1024))
    proc2 = subprocess.run([
      "gcloud", "beta", "compute", "ssh", "main",
      "--command", "cat | sudo tar -xzC /cms/",
      "--project", config.GCP_PROJ,
      "--zone", config.GCP_ZONE,
      "-q"
    ], input = proc1.stdout)
    

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
Usage: manage.py <start|stop|scale|query|exec|log|ranking> [args]

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

    Use this command to get public IP of the main instance.

exec:
    exec <main|worker*> command [command args]
    
    Run given command on the given GCP instance.

    Note: Each GCP instance runs Ubuntu 16.04, while cms services are running inside docker on the GCP instance. 
          Commands will be executed inside the Instance via ssh, NOT inside the docker container.

    Ex: ./manage.py exec worker0 sudo docker ps

log:
    log <cws|rws|worker*> [-f]
    
    Show log of given service.
    Use '-f' flag to follow the log

    cws: contest web server and log service
    rws: ranking web server
    worker*: worker

    Ex: ./manage.py log worker1
        ./manage.py log cws -f
    
ranking:
    ranking <send|get>
    
    send:
        Send logo, flags, and faces stored in 'ranking' folder to the server.
""")


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
        create_startup_script()
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
        create_startup_script()
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
    elif args[0] == 'exec':
        if len(args) == 1 or not (args[1] == 'main' or re.match(r"^worker(\d+)$",args[1])):
            print("[!] Unknown instance name.")
            print_usage()
            exit(1)
        elif len(args) == 2:
            print("[!] Shuould specify the command to execute.")
            print_usage()
            exit(1)
        command = " ".join(args[2:])
        run_on_instance(args[1], command)
    elif args[0] == 'ranking':
        if len(args) == 1:
            print("[!] Expect 'send' or 'get' operation")
            print_usage()
            exit(1)
        if args[1] == "send":
            send_ranking_data()
        else:
            print("[!] Operation should be one of 'send' or 'get'")
            print_usage()
            exit(1)
    elif args[0] == 'log':
        if len(args) == 1 or not (args[1] == 'rws' or args[1] == 'cws' or re.match(r"^worker(\d+)$",args[1])):
            print("[!] Unknown service name.")
            print_usage()
            exit(1)
        try:
            if args[1] == 'rws' or args[1] == 'cws':
                if len(args) > 2 and args[2] == '-f':
                    run_on_instance("main", "sudo docker logs -f " + args[1])
                else:
                    run_on_instance("main", "sudo docker logs " + args[1])
            else:
                if len(args) > 2 and args[2] == '-f':
                    run_on_instance(args[1], "sudo docker logs -f worker")
                else:
                    run_on_instance(args[1], "sudo docker logs worker")
        except KeyboardInterrupt:
            pass
    else:
        print("[!] Unknown command!")
        print_usage()
        exit(1)

print("[*] Done!")


