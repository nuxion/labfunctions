import asyncio
import time

import aiohttp

SERVICE = "http://localhost:8000"
CHUNK_SIZE = 4

timeout = aiohttp.ClientTimeout(total=30)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def fetch2(session, url, path):
    data = {"text": url}
    async with session.post(f"{SERVICE}/{path}", json=data) as response:
        await response.read()
        return response.status


async def fetch_all3(session, texts, path):
    async with aiohttp.ClientSession(timeout=timeout) as session:
        results = await asyncio.gather(
            *[fetch2(session, txt, path) for txt in texts], return_exceptions=True
        )
        return results


#


async def run(path, texts, chunks_size=CHUNK_SIZE):
    results = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for _, x in enumerate(chunks(texts, chunks_size)):
            res = await fetch_all3(session, x, path)
            results.extend(res)
    return results


async def measure(path, texts, chunks_size=4):
    start = time.time()
    results = await run(path, texts, chunks_size=chunks_size)
    end = time.time()
    ok = 0
    bad = 0
    for x in results:
        if x == 200:
            ok += 1
        else:
            bad += 1

    return dict(elapsed=end - start, ok=ok, bad=bad)
