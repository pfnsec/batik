import asyncio
import yaml
import json
import pydoc
import secrets
from threading import Thread
from typing import Any

from batik.api import Actor
from batik.api import ConcurrentLayer
from batik.api import Layer
from batik.api import Endpoint
from batik.api import Daemon
from batik.api import Trace, TraceStep

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
                else:
                    path  = step['name']
                    args  = step.get('args')
                    layer = Layer(self, path, args, next_layer)
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

        if trace:
            await trace.trace('result', res)
            await trace.finish()

        return res

    
    def broadcast(self, topic, data):
        print("Broadcast not implemented for current backend...")