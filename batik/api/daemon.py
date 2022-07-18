from batik.api import Layer
from batik.api.util import func_by_path, run_or_await

class Daemon:
    def __init__(self, name, manifest, path, args, endpoint, steps):
        self.name = name
        self.manifest = manifest
        self.pass_manifest = False
        self.actor = None
        self.args = args            
        self.endpoint = endpoint

        if path[0] == "$":
            # match $Actor.method , for example
            actor, fn = path[1:].split('.')
            self.actor = manifest.get_actor(actor).cl
            self.fn = getattr(self.actor, fn)
        else:
            # Match python function path
            self.fn = func_by_path(path)


    async def run(self, trace=False):
        # For every value produced by the generator fn()...
        args = self.args or {}
        async for res in await run_or_await(self.fn, **args):
            if(trace):
                trace = self.manifest.create_trace()
                await trace.trace(f"daemon/{self.name}", res)
            else: 
                trace = None
            # pass the result to its endpoint, if it exists
            if self.endpoint is not None:
                ep = self.manifest.get_endpoint(self.endpoint)
                await ep.run(res, trace=trace)
