# import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Optional
import cloudpickle
import httpx
from nb_workflows.conf import Config
from nb_workflows.utils import set_logger

logger = set_logger(__name__)
TASKID = "test5"
EXECUTIONID = "test"

VALID_STRATEGIES = ["local", "fileserver"]


@dataclass
class ExecContext:
    jobid: str
    executionid: str
    execution_dt: str


@dataclass
class CacheConfig:
    name: str
    ctx: ExecContext
    valid_for_min: int = 60
    strategy: str = "local"


def _write_pickle(name, data, ctx: ExecContext):
    fpath = f"/tmp/{ctx.jobid}.{ctx.executionid}.{name}.pickle"
    with open(fpath, "wb") as f:
        f.write(cloudpickle.dumps(data))
        logger.debug("CACHE: Wrote to %s", fpath)


def _restore_pickle(name, ctx: ExecContext):
    fpath = f"/tmp/{ctx.jobid}.{ctx.executionid}.{name}.pickle"
    try:
        with open(fpath, "rb") as f:
            data = cloudpickle.load(f)
            logger.debug("CACHE: Reading from %s", fpath)
            return data
    except EOFError:
        return None
    except FileNotFoundError:
        return None


def _write_fileserver(name, data, ctx: ExecContext):
    urlpath = f"{Config.FILESERVER}/cache/{ctx.jobid}.{ctx.executionid}.{name}"
    blob = cloudpickle.dumps(data)
    rsp = httpx.put(urlpath, content=blob)
    if rsp.status_code > 202:
        logger.warning("CACHE: writing to fileserver failed %s", urlpath)
    else:
        logger.debug("CACHE: wrote to fileserver %s", urlpath)


def _restore_fileserver(name, ctx: ExecContext):
    urlpath = f"{Config.FILESERVER}/cache/{ctx.jobid}.{ctx.executionid}.{name}"
    data = None

    try:
        rsp = httpx.get(urlpath)
        if rsp.status_code == 200:
            data = cloudpickle.loads(rsp.content)
            logger.debug("CACHE: Reading from fileserver %s", urlpath)
    except Exception as e:
        logger.warning(e)
    return data


def cache_manager_write(data, conf: CacheConfig):
    if conf.strategy == "local" and conf.ctx.jobid:
        _write_pickle(conf.name, data, conf.ctx)
    elif conf.strategy == "fileserver" and conf.ctx.jobid:
        _write_fileserver(conf.name, data, conf.ctx)
    else:
        logger.warning("CACHE: Invalid caching strategy %s", conf.strategy)


def cache_manager_read(conf: CacheConfig):
    data = None
    if conf.strategy == "local" and conf.ctx.jobid:
        data = _restore_pickle(conf.name, conf.ctx)
    elif conf.strategy == "fileserver" and conf.ctx.jobid:
        data = _restore_fileserver(conf.name, conf.ctx)
    else:
        logger.warning("CACHE: Invalid caching strategy %s", conf.strategy)
    return data


def build_context() -> ExecContext:
    jobid = globals().get("TASKID")
    execid = globals().get("TASKID")
    _now = datetime.utcnow().isoformat()
    now = globals().get("NOW", _now)
    return ExecContext(
        jobid=jobid,
        executionid=execid,
        execution_dt=now,
    )


def frozen_result(name, valid_for_min=60, strategy="local",
                  ctx: Optional[ExecContext] = None):
    if not ctx:
        ctx = build_context()

    cache_conf = CacheConfig(
        name=name,
        ctx=ctx,
        valid_for_min=valid_for_min,
        strategy=strategy
    )

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = cache_manager_read(cache_conf)
            if not result:
                result = func(*args, **kwargs)
                cache_manager_write(result, cache_conf)
            return result
        return wrapper
    return decorate


@frozen_result(name="my_func", strategy="fileserver")
def my_func(msg):
    print(msg)
    return msg*2


if __name__ == "__main__":
    my_func("hello world")
