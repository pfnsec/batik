import asyncio
import inspect
from batik.api.util import actor_by_path, func_by_path, run_or_await

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
            await trace.trace(f'layer/{self.path}', res)
        return res
    
    async def run_downstream(self, x, trace=None):
        res = await self.run(x, trace=trace)
        if self.next:
            return await self.next.run_downstream(res, trace=trace)
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
        else:
            self.sema = None

    async def run_downstream_sema(self, x, trace=None):
        if self.sema:
            async with self.sema:
                return await self.next.run_downstream(x, trace=trace)
        else:
            return await self.next.run_downstream(x, trace=trace)

    async def run_downstream(self, x, trace=None):
        tasks = []

        res = await self.run(x, trace=trace)
        if hasattr(res, "__aiter__"):
            async for x in res:
                task = asyncio.create_task(self.run_downstream_sema(x, trace=trace))
                tasks.append(task)
        else:
            for x in res:
                task = asyncio.create_task(self.run_downstream_sema(x, trace=trace))
                tasks.append(task)
        return await asyncio.gather(*tasks)