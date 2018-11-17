import yaml
import os
import sys

os.chdir(os.path.dirname(sys.path[0]))

class Config(object):
    def __init__(self,d):
        self.__dict__ = d

with open(os.path.join("config","config.yaml"),"r") as f:
    config = Config(yaml.safe_load(f))

