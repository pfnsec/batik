import asyncio

def prime_factors(n: int):
    if n <= 2:
        return []
    sieve = [True] * (n+1)
    for x in range(3, int(n**0.5) + 1, 2):
        for y in range(3, (n//x) + 1, 2):
            sieve[(x*y)]=False

    return [2] + [i for i in range(3, n, 2) if sieve[i]]

async def yield_triplets(x):
    yield x
    yield x * 2
    yield x * 3

async def sleep(x, secs = 1):
    await asyncio.sleep(secs)
    return x

def times_ten(x):
    print(x)
    return x * 10