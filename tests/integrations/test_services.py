import asyncio

import redis
import requests
from dataproc.conf import Config
from dataproc.utils import create_redis_client
from db.nosync import AsyncSQL
from db.sync import SQL


def test_services():
    """Testing real services"""
    db = SQL(Config.SQL)
    Session = db.sessionmaker()

    with Session() as session:
        result = session.execute("select * from alembic_version;")
        if result:
            print(f"1. Sync DB connection {result.one()[0]} ... [OK]")

    rq_conf = Config.rq2dict()
    rdb = redis.StrictRedis(
        host=rq_conf["host"], port=rq_conf["port"], db=rq_conf["db"]
    )
    rdb.set("test", "integration")
    rdb.delete("test")
    print("2. RQ redis connection ... [OK]")

    rdb_url = create_redis_client(Config.URL_REDIS)
    rdb_url.set("test", "integration")
    rdb_url.delete("test")
    print("3. URL Redis ... [OK]")

    r = requests.put(f"{Config.FILESERVER}/test/wehave3", data=b"hello")
    r2 = requests.delete(f"{Config.FILESERVER}/test/wehave3")
    if r.status_code == 201:
        print("4. Fileserver ... [OK]")
    else:
        raise KeyError(f"Fileserver error: {r.text}")

    r = requests.get(f"{Config.RAWSTORE}/status")
    if r.status_code == 200:
        print("5. Rawstore ... [OK]")
    else:
        raise KeyError(f"Rawstore error: {r.text}")

    r = requests.get(f"{Config.CRAWLER_SERVICE}/status")
    if r.status_code == 200:
        print("6. CRAWLER Service ... [OK]")
    else:
        raise KeyError(f"Crawler Service error: {r.text}")


async def dbasync():
    adb = AsyncSQL(Config.ASQL)
    await adb.init()
    session = adb.sessionmaker()
    async with session.begin():
        result = await session.execute("select * from alembic_version;")
        if result:
            print(f"7. ASync DB connection ... [OK]")


if __name__ == "__main__":
    test_services()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dbasync())
