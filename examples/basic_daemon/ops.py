import asyncio

async def tick(period=1):
    x = 0
    while True:
        await asyncio.sleep(period)
        yield x 
        x += 1


def log(x, source=None):
    print(f"{source}: {x}")
    return x