
import json
import aiohttp
from aiohttp import web

import asyncio

from batik import server

def custom_dumps(obj):
    return json.dumps(
        obj,
        default=str
    )

class HTTPServer(server.Server):

    def __init__(self, manifest):
        super().__init__(manifest)
        self.app = web.Application()
        self.add_routes()

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            print(msg.data)
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = msg.json()
                cmd = data['cmd']
                if cmd == 'invoke':
                    trace = self.manifest.create_trace()
                    task = asyncio.get_event_loop().create_task(
                        self.manifest.run_endpoint(
                            data['endpoint'], 
                            data['payload'],
                            cast=True,
                            trace=trace
                        )
                    )

                    while True:
                        trace_step = await trace.queue.get()
                        if trace_step == None: break
                        await ws.send_json({
                            'timestamp': trace_step.timestamp.isoformat(),
                            'node': trace_step.node,
                            'data': trace_step.data,
                        }, dumps=custom_dumps)
                        trace.queue.task_done()
                    await asyncio.gather(task)
                    await ws.send_str('goodbye')

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                    ws.exception())

        return ws

    # Get all endpoints
    async def get_endpoints(self, request):
        res = {
            'endpoints': list(self.manifest.endpoints.keys())
        }
        return web.json_response(res)

    async def get_endpoint(self, request):
        endpoint = request.match_info['endpoint']
        if endpoint not in self.manifest.endpoints:
            raise aiohttp.web.HTTPNotFound()
        else:
            ep = self.manifest.get_endpoint(endpoint)
            layers = []
            for layer in ep.layers():
                layers.append({''})
            res = {
                'layers': layers
            }
            return web.json_response(res)
    
    async def run_endpoint(self, request):
        endpoint = request.match_info['endpoint']
        if endpoint not in self.manifest.endpoints:
            raise aiohttp.web.HTTPNotFound()

        if request.body_exists:
            payload = await request.json()
            print(payload)

        trace = self.manifest.create_trace()
        asyncio.get_event_loop().create_task(
            self.manifest.run_endpoint(
                endpoint, payload,
                cast=True,
                trace=trace
            )
        )
        res = {
            'trace_id': trace.key
        }
        return web.json_response(res)

    async def get_traces(self, request):
        res = {
            'traces': list(self.manifest.traces.keys())
        }
        return web.json_response(res)

    async def get_trace(self, request):
        trace_id = request.match_info['trace']
        trace = self.manifest.get_trace(trace_id)
        if trace is None:
            raise aiohttp.web.HTTPNotFound()
        else:
            res = {
                'trace_id': trace_id
            }
            return web.json_response(res)


    def add_routes(self):
        self.app.add_routes([
            web.get('/ws/', self.websocket_handler),
            web.get('/endpoint/', self.get_endpoints),
            web.get('/endpoint/{endpoint}', self.get_endpoint),
            web.post('/endpoint/{endpoint}/run', self.run_endpoint),
            web.get('/trace/', self.get_traces),
            web.get('/trace/{trace}', self.get_trace),
        ])

    async def run(self):
        runner = aiohttp.web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8086)
        await site.start()
        await self.manifest.daemon_task(trace=True)
        while True:
            await asyncio.sleep(1)

