import yaml
import os

class Config(object):
    def __init__(self,d):
        self.__dict__ = d

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.dirname(dname))

with open(os.path.join("config","config.yaml"),"r") as f:
    config = Config(yaml.safe_load(f))
