import datetime
import asyncio

class TraceStep:
    def __init__(self, node, data):
        self.timestamp = datetime.datetime.now()
        self.node = node
        self.data = data
        #print(self.timestamp, node, data)

# Trace a call through the compute graph.
class Trace:
    def __init__(self, source):
        self.path = []
        self.queue = asyncio.Queue()

    async def trace(self, node, data):
        step = TraceStep(node, data)
        self.path.append(step)
        await self.queue.put(step)

    async def finish(self):
        await self.queue.put(None)
