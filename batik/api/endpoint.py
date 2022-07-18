from typing import Any
import inspect

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
            await trace.trace(f'endpoint/{self.name}', x)

        return await self.layer.run_downstream(x, trace=trace)