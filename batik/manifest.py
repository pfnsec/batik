import yaml
#import ray
import importlib
import pydoc
import json
import re
import sys


def actor_by_path(name):

    module_name, class_name = name.split(".")

    if './' not in sys.path:
        sys.path.append('./')

    if module_name in sys.modules:
        somemodule = importlib.reload(sys.modules[module_name])
    else:
        somemodule = importlib.import_module(module_name)

    cl = getattr(somemodule, class_name)

    return cl


def func_by_path(name, *args, **kwargs):

    ns = name.split(".")

    module_name = '.'.join(ns[0:-1])
    func_name   = ns[-1]

    if './' not in sys.path:
        sys.path.append('./')

    if module_name in sys.modules:
        somemodule = importlib.reload(sys.modules[module_name])
    else:
        somemodule = importlib.import_module(module_name)

    fn = getattr(somemodule, func_name)

    return fn

def parse_from_file():
    with open("./batik.yaml") as manifest:
        mfst = yaml.load(manifest, Loader=yaml.FullLoader)
        return parse(mfst)

def parse(mfst):

    state = {}
    state['actors'] = {}
    state['endpoints'] = {}
    state['daemons'] = []

    for actor in mfst.get('actors') or []:
        name = actor["name"]
        class_path = actor["class"]
        args = actor.get("args")

        state['actors'][name] = actor_by_path(class_path)(layer_args=args)


    for endpoint in mfst.get('endpoints') or []:
        steps = []

        for step in endpoint['steps']:
            name = step['name']

            # $Inst.method , for example
            if name[0] == "$":
                class_path, fn = name[1:].split('.')
                actor = state["actors"][class_path]
                #steps.append((getattr(actor, fn).remote, step))
                steps.append({
                    "actor": actor,
                    "fn": getattr(actor, fn),
                    "args": step
                    })
            else:
                # Match python function path

                fn = func_by_path(name)
                steps.append({
                    "fn": fn, 
                    "args": step})


                #fn = name.split('.')[-1]

        state['endpoints'][endpoint['name']] = {}
        state['endpoints'][endpoint['name']]["steps"] = steps
        state['endpoints'][endpoint['name']]["input_type"] = endpoint.get("input_type") or 'str'

    for daemon in mfst.get('daemons') or []:
        name = daemon["name"]
        args = daemon.get("args")
        endpoint = daemon["endpoint"]

        # $Inst.method , for example
        if name[0] == "$":
            class_path, fn = name[1:].split('.')
            actor = state["actors"][class_path]

            step = {
                "actor": actor,
                "fn": getattr(actor, fn),
                "args": args
            }

        else:
            # Match python function path

            fn = func_by_path(name)
            step = {
                "fn": fn, 
                "args": args
            }

        state["daemons"].append({
            "name": name,
            "endpoint": endpoint,
            "fn": step["fn"],
            "args": step["args"],
        })

    
    return state


def daemon_thread(state, daemon):
    endpoint = daemon['endpoint']
    for res in daemon['fn']():
        endpoint_run(state, endpoint, res)


def endpoint_run(state, endpoint, payload):
    steps = state['endpoints'][endpoint]['steps']
    input_type = state['endpoints'][endpoint]['input_type']

    # do this cast in serve()!

#   if input_type == "json":
#       payload = json.loads(payload)
#   else:
#       # Cast from a 'POST' body to the type specified in the 
#       # manifest.
#       payload = pydoc.locate(input_type)(payload)

    res = payload

    for step in steps:
        # TODO: if "group" in step...
        # TODO: insert expanded layer kwargs from 'step'
        res = step["fn"](res)

    return res


def endpoint_run_ray(state, endpoint, *args, **kwargs):
    steps = state['endpoints'][endpoint]

    fn, kw = steps[0]
    kw.pop("name", None)
    res = fn(*args, **kwargs, **kw)

    for step in steps[1:]:
        fn, kw = step
        kw.pop("name", None)
        res = fn(res, **kw)

    return ray.get(res)


#state = parse_from_file()

class Manifest:
    def __init__(self):
        self.state = state
    
    def reconfigure(self, config):
        self.endpoint = config['endpoint']

    def __call__(self, request):
        return endpoint_run(self.state, self.endpoint, request)