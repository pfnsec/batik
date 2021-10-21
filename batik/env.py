import os 
from os.path import expanduser

import yaml

batik_env = {}
env = batik_env.get

def set_env_file(file):
    global batik_env

    with open(file, 'r') as stream:
        try:
            batik_env = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

global_env = os.path.join(expanduser("~"), "batik.env.yaml")

# TODO eventually check other paths?
if(os.path.exists("./batik.env.yaml")):
    set_env_file("./batik.env.yaml")
elif(os.path.exists(global_env)):
    set_env_file(global_env)