from typing import Any
import yaml
import secrets
import importlib
import inspect
import asyncio
import datetime

import pydoc
import json
import re
import sys
from threading import Thread
import concurrent


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


async def run_or_await(fn, *args, **kwargs):
    if inspect.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    else:
        return fn(*args, **kwargs)

class Layer:
    def __init__(self, manifest, path, kwargs, next):
        self.path = path
        self.manifest = manifest
        self.pass_manifest = False
        self.actor = None
        self.kwargs = kwargs 
        # Reference to the next layer in the linked-list
        self.next = next 

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

    async def run(self, x, trace=None):
        kwargs = self.kwargs or {}
        # TODO: Pass the trace in here too!
        if self.pass_manifest:
            res = await run_or_await(self.fn, x, **kwargs, batik_manifest=self.manifest)
        else:
            res = await run_or_await(self.fn, x, **kwargs)
        if trace:
            trace.trace(f'layer/{self.path}', res)
        return res
    
    async def run_downstream(self, x, trace=None):
        res = await self.run(x, trace=trace)
        if self.next:
            return await self.next.run(res, trace=trace)
        else:
            return res


# A layer that runs its downstream tasks concurrently, with 
# an optional semaphore to limit the number of tasks running
class ConcurrentLayer(Layer):
    def __init__(self, manifest, path, kwargs, next, concurrency=None):
        super().__init__(manifest, path, kwargs, next)
        self.concurrency = concurrency
        if concurrency:
            self.sema = asyncio.BoundedSemaphore(concurrency)

    async def run_downstream_sema(self, x, trace=None):
        if self.sema:
            async with self.sema:
                return await self.next.run_downstream(x, trace=trace)
        else:
            return await self.next.run_downstream(x, trace=trace)

    async def run_downstream(self, x, trace=None):
        tasks = []

        res = await self.run(x, trace=trace)
        print("run_downstream", res)
        if hasattr(res, "__aiter__"):
            async for x in res:
                task = asyncio.create_task(self.run_downstream_sema(x, trace=trace))
                tasks.append(task)
        else:
            for x in res:
                task = asyncio.create_task(self.run_downstream_sema(x, trace=trace))
                tasks.append(task)
        return await asyncio.gather(*tasks)

class Actor:
    # Actor's kwargs are contained within the underlying actor class
    def __init__(self, class_path, kwargs):
        if kwargs is None:
            self.cl = actor_by_path(class_path)()
        else:
            self.cl = actor_by_path(class_path)(**kwargs)


class Endpoint:
    def __init__(self, name, layer):
        self.name = name
        self.layer = layer

    # Cast an input variable to the type annotated by
    # the first layer of the endpoint.
    def cast(self, x: Any):
        fn = self.layer.fn
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())
        annotation = params[0].annotation
        if annotation == inspect._empty:
            return x
        else:
            return annotation(x)

    async def run(self, x, trace=None):
        if trace:
            trace.trace(f'endpoint/{self.name}', x)

        return await self.layer.run_downstream(x, trace=trace)


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

    async def run(self, trace=False):
        # For every value produced by the generator fn()...
        args = self.args or {}
        async for res in await run_or_await(self.fn, **args):
            if(trace):
                trace = self.manifest.create_trace()
                trace.trace(f"daemon/{self.name}", res)
            else: 
                trace = None
            # Run it through its layers...
            for layer in self.layers:
                res = await layer.run(res, trace=trace)
            # ... and pass the result to its endpoint, if it exists
            if self.endpoint is not None:
                ep = self.manifest.get_endpoint(self.endpoint)
                await ep.run(res, trace=trace)


class TraceStep:
    def __init__(self, node, data):
        self.timestamp = datetime.datetime.now()
        self.node = node
        self.data = data
        print(self.timestamp, node, data)

# Trace a call through the compute graph.
class Trace:
    def __init__(self, source):
        self.path = []

    def trace(self, node, data):
        self.path.append(TraceStep(node, data))


class Manifest:
    def __init__(self):
        self.alias = ""
        self.actors = {}
        self.endpoints = {}
        self.daemons = {}
        self.traces = {}
    
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

            next_layer = None
            for step in list(reversed(endpoint['steps'])):
                # Janky, janky notation to signify a 
                # [concurrent] generator function
                if isinstance(step['name'], list):
                    path  = step['name'][0]
                    # Hey guy, why not just use step['concurrency'] ????
                    if len(step['name']) > 1:
                        concurrency = step['name'][1]
                    else:
                        concurrency = None
                    args  = step.get('args')
                    layer = ConcurrentLayer(self, path, args, next_layer, concurrency=concurrency)
                    print(layer)
                else:
                    path  = step['name']
                    args  = step.get('args')
                    layer = Layer(self, path, args, next_layer)
                    print(layer)
                next_layer = layer

            ep = Endpoint(name, layer)

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
    
    def get_actor(self, name: str) -> Actor:
        return self.actors[name]

    def add_endpoint(self, endpoint: Endpoint, name: str):
        self.endpoints[name] = endpoint

    def get_endpoint(self, name: str) -> Endpoint:
        return self.endpoints[name]
    
    def add_daemon(self, daemon: Daemon, name: str):
        self.daemons[name] = daemon

    def get_daemon(self, name: str) -> Daemon:
        return self.daemons[name]


    def spawn_daemons(self):
        for daemon in self.daemons:
            daemon_worker = Thread(target=self.daemon_thread, args=(daemon,))
            daemon_worker.setDaemon(True)
            daemon_worker.start()
    

    async def daemon_task(self, trace=False):
        for daemon in self.daemons.keys():
            asyncio.get_event_loop().create_task(
                self.daemons[daemon].run(trace=trace)
            )
    

    # Cast from a 'POST' body to the type specified in the manifest.
    def cast_endpoint_payload(self, name: str, payload: Any):
        input_type = self.endpoints[name].input_type

        if input_type == "json":
            payload = json.loads(payload)
        else:
            payload = pydoc.locate(input_type)(payload)

        return payload


    def create_trace(self) -> str:
        key = secrets.token_urlsafe(10)
        while key in self.traces:
            key = secrets.token_urlsafe(10)
        trace = Trace(key)
        self.traces[key] = trace
        return trace

    def get_trace(self, key: str) -> Trace:
        return self.traces.get(key)


    async def run_endpoint(self, name: str, payload: Any, cast=False, trace=None):

        ep = self.endpoints[name]

        payload = ep.cast(payload)

        res = await ep.run(payload, trace=trace)

        return res

    
    def broadcast(self, topic, data):
        print("Broadcast not implemented for current backend...")
