import asyncio
import logging
import pickle
import resource
import socket
from datetime import datetime
from functools import wraps
from glob import glob
from importlib import import_module
from time import time

import redis
from rq import Queue

from nb_workflows.conf import Config
from nb_workflows.hashes import PasswordScript

_formats = {"hours": "%Y%m%d.%H%M%S", "day": "%Y%m%d", "month": "%Y%m"}


def list_workflows():
    notebooks = []
    files = glob(f"{Config.BASE_PATH}/{Config.NB_WORKFLOWS}*")
    for x in files:
        if ".ipynb" or ".py" in x:
            notebooks.append(x.split("/")[-1].split(".")[0])
    return notebooks


def today_string(utc=True, format_="hours"):
    if utc:
        _now = datetime.utcnow().strftime(_formats[format_])
    else:
        _now = datetime.now().strftime(_formats[format_])
    return _now


def test_error():
    import os

    pid = os.getpid()
    print("From pid: ", pid)

    raise TypeError("error from test_error")


def queue_init(redis, name="default"):
    return Queue(name, connection=redis.Redis(**redis))


def check_port(ip: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    if result != 0:
        return False
    return True


async def run_async(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    rsp = await loop.run_in_executor(None, func, *args, **kwargs)
    return rsp


def init_blueprints(app, blueprints_allowed):
    blueprints = set()
    mod = app.__module__
    for mod_name in blueprints_allowed:
        module = import_module(f"nb_workflows.{mod_name}.web", mod)
        bp = getattr(module, f"{mod_name}_bp")
        blueprints.add(bp)

    for bp in blueprints:
        print("Adding blueprint: ", bp.name)
        app.blueprint(bp)


def get_query_param(request, key, default_val=None):
    val = request.args.get(key, [default_val])
    return val[0]


def parse_page_limit(request, def_pg="1", def_lt="100"):
    strpage = request.args.get("page", [def_pg])
    strlimit = request.args.get("limit", [def_lt])
    page = int(strpage[0])
    limit = int(strlimit[0])

    return page, limit


def mem():
    """from https://stackoverflow.com/questions/32167386/force-garbage-collection-in-python-to-free-memory"""
    print(
        "Memory usage         : % 2.2f MB"
        % round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)
    )


def format_bytes(n: int) -> str:
    """Format bytes as text

    >>> from dask.utils import format_bytes
    >>> format_bytes(1)
    '1 B'
    >>> format_bytes(1234)
    '1.21 kiB'
    >>> format_bytes(12345678)
    '11.77 MiB'
    >>> format_bytes(1234567890)
    '1.15 GiB'
    >>> format_bytes(1234567890000)
    '1.12 TiB'
    >>> format_bytes(1234567890000000)
    '1.10 PiB'

    For all values < 2**60, the output is always <= 10 characters.
    """
    for prefix, k in (
        ("Pi", 2**50),
        ("Ti", 2**40),
        ("Gi", 2**30),
        ("Mi", 2**20),
        ("ki", 2**10),
    ):
        if n >= k * 0.9:
            return f"{n / k:.2f} {prefix}B"
    return f"{n} B"


def mem_obj(obj):
    return format_bytes(len(pickle.dumps(obj)))


def mem_df(df):
    return format_bytes(sum(df.memory_usage(deep=True).tolist()))


def flatten_list(list_):
    return [item for sublist in list_ for item in sublist]


def set_logger(name: str, level=Config.LOGLEVEL):
    l = logging.getLogger(name)
    _level = getattr(logging, level)
    l.setLevel(_level)
    return l


def Timeit(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        # print('func:%r args:[%r, %r] took: %2.4f sec' %
        #      (f.__name__, args, kw, te-ts))
        e = round(te - ts, 5)
        print(f"func: {f.__name__} took: {e} sec")
        return result

    return wrap


def Memit(f):
    @wraps(f)
    def wrap(*args, **kw):
        mem()
        result = f(*args, **kw)
        # print(f"func: {f.__name__} took: {e} sec")
        mem()
        return result

    return wrap


def create_redis_client(fullurl, decode_responses=True) -> redis.Redis:
    """Returns a redis client. The format of the url
    is like: redis://localhost:6379/0
    """
    url = fullurl.split("redis://")[1]
    h, port_db = url.split(":")
    p, db = port_db.split("/")
    return redis.StrictRedis(
        host=h, port=p, db=db, decode_responses=decode_responses
    )


def password_manager() -> PasswordScript:
    s = Config.SALT
    return PasswordScript(salt=s.encode("utf-8"))
