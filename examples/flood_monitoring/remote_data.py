
import altair
import datetime
import aiohttp
import asyncio
from pprint import pprint

import pandas as pd
import numpy as np

root_url = "http://environment.data.gov.uk/flood-monitoring/"


async def station_history(station_id=None):
    index = 0
    resp = await station_history_chunk(index, station_id=station_id)
    dt_1 = None

    data = []

    while len(resp['items']) > 0:
        index += 1
        resp = await station_history_chunk(index, station_id=station_id)

        for m in resp['items']:
            dt = datetime.datetime.fromisoformat(m['dateTime'].replace('Z', ''))
            #if(dt_1 is not None): 
                #print(dt_1 - dt)
            dt_1 = dt

            data.append([dt, float(m['value'])])
    
    data = np.array(data)

    df = pd.DataFrame({'time': data[:,0], 'reading': data[:,1]})
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    print(df.index.max())

    chart = altair.Chart(df).mark_line().encode(
        x='time',
        y='reading'
    )

    chart

    print(df.index)
    return df
    

async def station_history_chunk(index: int, station_id=None, chunk_size=500):

    since = datetime.datetime.now() - datetime.timedelta(days = 1000)

    url = root_url + f"id/stations/{station_id}/readings"

    params = {
        'since': since.isoformat(),
        '_sorted': '',
        '_limit': chunk_size,
        '_offset': index * chunk_size,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            resp = await resp.json()
            return resp


asyncio.run(station_history(station_id=51107))