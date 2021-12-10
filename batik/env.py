import os 
from os.path import expanduser

import yaml

env = {}
env_path = None

def set_env_file(file):
    global env

    if env_path is None: return

    with open(file, 'r') as stream:
        try:
            env = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

global_env = os.path.join(expanduser("~"), "batik.env.yaml")

# TODO eventually check other paths?
if(os.path.exists("./batik.env.yaml")):
    env_path = "./batik.env.yaml"
elif(os.path.exists(global_env)):
    env_path = global_env

set_env_file(env_path)
