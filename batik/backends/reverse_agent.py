import json
import aiohttp
from aiohttp import web


import asyncio

import batik
from batik import server
from batik.api.message import InvokeTrace, message_from_dict
from batik.api.message import Message
from batik.api.message import InvokeRequest, InvokeResponse


def custom_dumps(obj):
    return json.dumps(
        obj,
        default=str
    )

class ReverseAgent(server.Server):
    def __init__(self, manifest):
        super().__init__(manifest)

    async def apply_message(self, ws, message):
        if isinstance(message, InvokeRequest):
            if(message.trace):
                trace = self.manifest.create_trace()
            else:
                trace = None

            task = asyncio.get_event_loop().create_task(
                self.manifest.run_endpoint(
                    message.endpoint, 
                    message.payload,
                    cast=True,
                    trace=trace
                )
            )

            while True:
                trace_step = await trace.queue.get()
                if trace_step == None: break
                await ws.send_json(InvokeTrace(
                    trace_step.node,
                    trace_step.timestamp.isoformat(),
                    trace_step.data,
                    message.tag
                ).to_dict(), dumps=custom_dumps)
                await ws.send_json(InvokeResponse(
                    res, message.tag
                ).to_dict(), dumps=custom_dumps)
                trace.queue.task_done()

            res = await asyncio.gather(task)

            await ws.send_json(InvokeResponse(
                res, message.tag
            ).to_dict(), dumps=custom_dumps)


    async def run(self):
        await self.manifest.daemon_task(trace=False)
        headers = {'namespace': 'saturn'}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.ws_connect('http://localhost:8086/substring/') as ws:
                try: 
                    await ws.send_json(InvokeResponse(
                        "test!", "arg!!" 
                    ).to_dict(), dumps=custom_dumps)
                    await ws.send_json(InvokeResponse(
                        "test!", "aaaarg!" 
                    ).to_dict(), dumps=custom_dumps)
                    async for msg in ws:
                        print(msg.json())
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self.apply_message(ws, msg.json())
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"ws connection closed with exception {ws.exception()}")
                            break
                finally:
                    print("Disconnected...")
