import asyncio
import codecs
import logging
import os
import pickle
import re
import resource
import socket
import subprocess
import sys
import unicodedata
from datetime import datetime
from functools import wraps
from importlib import import_module
from pathlib import Path
from time import time

import redis
import toml
import yaml

from nb_workflows.conf import defaults
from nb_workflows.errors import CommandExecutionException

_formats = {"hours": "%Y%m%d.%H%M%S", "day": "%Y%m%d", "month": "%Y%m"}
_filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
_windows_device_files = (
    "CON",
    "AUX",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "LPT1",
    "LPT2",
    "LPT3",
    "PRN",
    "NUL",
)


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


def run_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    rsp = loop.run_until_complete(func(*args, **kwargs))
    return rsp


def init_blueprints(app, blueprints_allowed):
    """It import and mount each module inside `nb_workflows.web`
    which ends with _bp.

    """
    blueprints = set()
    mod = app.__module__
    for mod_name in blueprints_allowed:
        module = import_module(f"nb_workflows.web.{mod_name}_bp", mod)
        for el in dir(module):
            if el.endswith("_bp"):
                bp = getattr(module, el)
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
    return redis.StrictRedis(host=h, port=p, db=db, decode_responses=decode_responses)


def secure_filename(filename: str) -> str:
    r"""Pass it a filename and it will return a secure version of it.  This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.
    On windows systems the function also makes sure that the file is not
    named after one of the special device files.
    >>> secure_filename("My cool movie.mov")
    'My_cool_movie.mov'
    >>> secure_filename("../../../etc/passwd")
    'etc_passwd'
    >>> secure_filename('i contain cool \xfcml\xe4uts.txt')
    'i_contain_cool_umlauts.txt'
    The function might return an empty filename.  It's your responsibility
    to ensure that the filename is unique and that you abort or
    generate a random filename if the function returned an empty one.
    .. versionadded:: 0.5
    :param filename: the filename to secure
    """
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip(
        "._"
    )

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if (
        os.name == "nt"
        and filename
        and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = f"_{filename}"

    return filename


def get_parent_folder():
    """Get only the name of the parent folder
    commonly used to define the project name
    """
    root = Path(os.getcwd())
    return str(root).rsplit("/", maxsplit=1)[-1]


def open_toml(filepath: str):
    with open(filepath, "r") as f:
        tf = f.read()

    tomconf = toml.loads(tf)
    return tomconf


def write_toml(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        _dump = toml.dumps(data)
        f.write(_dump)


def open_yaml(filepath: str):
    with open(filepath, "r") as f:
        data = f.read()
        dict_ = yaml.safe_load(data)

    return dict_


def write_yaml(filepath: str, data, *args, **kwargs):
    with open(filepath, "w") as f:
        dict_ = yaml.dump(data, *args, **kwargs)
        f.write(dict_)


def set_logger(name: str, level: str):
    logger = logging.getLogger(name)
    _level = getattr(logging, level)
    logger.setLevel(_level)
    return logger


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def execute_cmd(cmd) -> str:
    """Wrapper around subprocess"""
    with subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as p:

        out, err = p.communicate()
        if err:
            raise CommandExecutionException(err.decode())

        return out.decode().strip()


def path_relative(fp):
    """Given a  filepath returns a normalized a path"""
    return str(Path(fp))


def fullpath(fp):
    """Returns a fullpath based on the BASE_PATH env"""
    base_p = os.getenv(defaults.BASE_PATH_ENV)
    return str(Path(f"{base_p}/{fp}").resolve())


def mkdir_p(fp):
    """Make the fullpath
    similar to mkdir -p in unix systems.
    """
    Path(fp).mkdir(parents=True, exist_ok=True)


def parent_folder():
    return str(Path("../").resolve())


def under_virtualenv() -> bool:
    if sys.prefix == sys.base_prefix:
        return False
    return True


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path="__version__.py"):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


def parse_var_line(line):
    """
    This regex works only if spaces are not used
     ^(\w*)=?*(['|"].*?['|"|])$
    """
    k = line.split("=", maxsplit=1)[0].strip()
    v = line.split("=", maxsplit=1)[1].replace('"', "").strip("\n").strip()
    return k, v


def format_seconds(secs) -> str:
    ago = f"{round(secs)} seconds ago"
    if secs > 60 and secs < 3600:
        ago = f"{round(secs / 60)} minutes ago"
    elif secs >= 3600:
        ago = f"{round((secs / 60)/ 60)} hours ago"
    return ago


def binary_file_reader(fp: str, chunk_size=1024):
    """
    File reader generator mostly used for projects upload
    """
    with open(fp, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data
