import aiohttp
import json
from .base import Base


class Invoke(Base):
    """Invoke endpoints"""

    async def run(self):
        endpoint = self.options["<endpoint>"]

        use_json = self.options.get("--json") or None
        if use_json:
            with open(self.options["<file>"]) as json_file:
                payload = json.load(json_file)
        else:
            payload = self.options.get("<payload>") or None

        data = {
            'cmd': 'invoke',
            'endpoint': endpoint,
            'payload': payload,
        }

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect('http://localhost:8086/ws/') as ws:
                await ws.send_json(data)

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == 'goodbye':
                            await ws.close()
                            break
                        else:
                            print(msg.json())
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break