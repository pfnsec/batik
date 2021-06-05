import yaml
#import ray
import importlib
import pydoc
import re
import sys



def actor_by_path(name):

    module_name, class_name = name.split(".")

    if './' not in sys.path:
        sys.path.append('./')

    somemodule = importlib.import_module(module_name)

    cl = getattr(somemodule, class_name)

    return cl


def func_by_path(name, *args, **kwargs):

    ns = name.split(".")

    module_name = '.'.join(ns[0:-1])
    func_name   = ns[-1]

    if './' not in sys.path:
        sys.path.append('./')

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

    for actor in mfst.get('actors') or []:
        name = actor["name"]
        class_path = actor["class"]
        args = actor.get("args")

        state['actors'][name] = actor_by_path(class_path)(layer_args=args)


    for endpoint in mfst['endpoints']:
        steps = []

        for step in endpoint['steps']:
            name = step['name']

            # $Inst.method
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
    
    return state


def parse_old(mfst):

    state = {}
    state['actors'] = {}
    state['endpoints'] = {}

    for endpoint in mfst['endpoints']:
        steps = []

        for step in endpoint['steps']:
            #print(step)
            name = step['name']

            if ':' in name:
                inst = step.get('inst') or 'default'

                path, fn = name.split(':')

                inst_path = f'{path}_{inst}'

                actor = state['actors'].get(inst_path)
                if not actor:
                    actor = actor_by_path(path)(layer_args=step)
                    state['actors'][inst_path] = actor
                
                # Don't insert these args for now... we init with them, after all.
                #steps.append((getattr(actor, fn).remote, step))
                steps.append((getattr(actor, fn).remote, {}))

            else:
                # Match python function path

                fn = func_by_path(name)
                steps.append((fn, step))


                #fn = name.split('.')[-1]

        state['endpoints'][endpoint['name']] = steps

    return state

def endpoint_run(state, endpoint, payload):
    steps = state['endpoints'][endpoint]['steps']
    input_type = state['endpoints'][endpoint]['input_type']


    payload = pydoc.locate(input_type)(payload)

    res = payload


    for step in steps:

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