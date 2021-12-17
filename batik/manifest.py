from typing import Any
import yaml
#import ray
import importlib
import inspect

import pydoc
import json
import re
import sys
from threading import Thread


def actor_by_path(name):
    print(f"Actor by path {name}")
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



class Layer:
    def __init__(self, manifest, path, args):
        self.manifest = manifest
        self.pass_manifest = False
        self.actor = None
        self.args = args 

        if path[0] == "$":
            # match $Actor.method , for example
            actor, fn = path[1:].split('.')
            self.actor = manifest.get_actor(actor).cl
            self.fn = getattr(self.actor, fn)
        else:
            # Match python function path
            self.fn = func_by_path(path)

        sig = inspect.signature(self.fn)
        if 'batik_manifest' in sig.parameters:
            self.pass_manifest = True

    def run(self, x):
        if self.pass_manifest:
            return self.fn(x, batik_manifest=self.manifest)
        else:
            return self.fn(x)


class Actor:
    # Actor's layer_args are contained within the underlying actor class
    def __init__(self, class_path, args):
        if args is None:
            self.cl = actor_by_path(class_path)()
        else:
            self.cl = actor_by_path(class_path)(**args)


class Endpoint:
    def __init__(self):
        self.layers = []
    
    def add_layer(self, layer: Layer):
        self.layers.append(layer)

    # Cast an input variable to the type annotated by
    # the first layer of the endpoint.
    def cast(self, x: Any):
        fn = self.layers[0].fn
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())
        annotation = params[0].annotation
        if annotation == inspect._empty:
            return x
        else:
            return annotation(x)

    def run(self, x):
        y = x
        for layer in self.layers:
            y = layer.run(y)
        return y

class Daemon:
    def __init__(self, name, manifest, path, args, endpoint, steps):
        self.name = name
        self.manifest = manifest
        self.pass_manifest = False
        self.actor = None
        self.args = args            
        self.endpoint = endpoint
        self.layers = []

        if path[0] == "$":
            # match $Actor.method , for example
            actor, fn = path[1:].split('.')
            self.actor = manifest.get_actor(actor).cl
            self.fn = getattr(self.actor, fn)
        else:
            # Match python function path
            self.fn = func_by_path(path)

        if steps is not None:
            for step in steps:
                path = step['name']
                args = step.get('args')
                layer = Layer(manifest, path, args)
                self.layers.append(layer)

    def run(self):
        # For every value produced by the generator fn()...
        for res in self.fn(**self.args):
            trace = Trace(f'daemon/{self.name}')
            # Run it through its layers...
            for layer in self.layers:
                res = layer.run(res)
            # ... and pass the result to its endpoint, if it exists
            if self.endpoint is not None:
                ep = self.manifest.get_endpoint(self.endpoint)
                ep.run(res)

# Trace a call through the compute graph.
class Trace:
    def __init__(self, source):
        self.source = source
        self.path = []

    def trace(self, ):
        pass

class Manifest:
    def __init__(self):
        self.alias = ""
        self.actors = {}
        self.endpoints = {}
        self.daemons = {}
    
    def parse_file(self):
        with open("./batik.yaml") as manifest:
            mfst = yaml.load(manifest, Loader=yaml.FullLoader)
            self.alias = mfst['alias']
            return self.parse(mfst)

    def parse(self, mfst):
        for actor in mfst.get('actors') or []:
            name       = actor["name"]
            class_path = actor["class"]
            args       = actor.get("args")

            act = Actor(class_path, args)

            self.add_actor(act, name)

        for endpoint in mfst.get('endpoints') or []:
            name = endpoint['name']
            input_type = endpoint.get("input_type") or 'str'

            ep = Endpoint()

            for step in endpoint['steps']:
                path  = step['name']
                args  = step.get('args')
                layer = Layer(self, path, args)
                ep.add_layer(layer)

            self.add_endpoint(ep, name)


        for daemon in mfst.get('daemons') or []:
            name      = daemon["name"]
            generator = daemon["generator"]
            args      = daemon.get("args")
            endpoint  = daemon.get("endpoint")
            steps     = daemon.get("steps")

            dm = Daemon(name, self, generator, args, endpoint, steps)

            self.add_daemon(dm, name)


    def add_actor(self, actor: Actor, name: str):
        self.actors[name] = actor
    
    def get_actor(self, name: str):
        return self.actors[name]

    def add_endpoint(self, endpoint: Endpoint, name: str):
        self.endpoints[name] = endpoint

    def get_endpoint(self, name: str):
        return self.endpoints[name]
    
    def add_daemon(self, daemon: Daemon, name: str):
        self.daemons[name] = daemon

    def get_daemon(self, name: str):
        return self.daemons[name]




    def spawn_daemons(self):
        for daemon in self.daemons:
            daemon_worker = Thread(target=self.daemon_thread, args=(daemon,))
            daemon_worker.setDaemon(True)
            daemon_worker.start()
    

    # Cast from a 'POST' body to the type specified in the manifest.
    def cast_endpoint_payload(self, name: str, payload: Any):
        input_type = self.endpoints[name].input_type

        if input_type == "json":
            payload = json.loads(payload)
        else:
            payload = pydoc.locate(input_type)(payload)

        return payload


    def run_layer_set(self, layers, payload: Any):
        res = payload
        for layer in layers:
            if layer.pass_manifest:
                res = layer.fn(res, batik_manifest=self)
            else:
                res = layer.fn(res)
        return res

    
    def run_endpoint(self, name: str, payload: Any, cast=False):

        ep = self.endpoints[name]

        payload = ep.cast(payload)

        res = ep.run(payload)

        return res
    
    def broadcast(self, topic, data):
        print("Broadcast not implemented for current backend...")
