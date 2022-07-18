import os 
from os.path import expanduser

import yaml

env = {}
env_path = None

def load_env_file(file):
    global env

    if env_path is None: return

    with open(file, 'r') as stream:
        env = yaml.safe_load(stream)

if(os.path.exists("./batik.env.yaml")):
    env_path = "./batik.env.yaml"
    load_env_file(env_path)
