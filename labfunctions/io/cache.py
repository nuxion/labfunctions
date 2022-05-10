# import tempfile
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

import cloudpickle
import httpx

from labfunctions.conf.client_settings import settings

# from labfunctions.workflows.core import build_context
from labfunctions.types import SimpleExecCtx

logger = logging.getLogger(__name__)

VALID_STRATEGIES = ["local", "fileserver"]


@dataclass
class CacheConfig:
    name: str
    ctx: SimpleExecCtx
    valid_for_min: int = 60
    strategy: str = "local"


def build_ctx_global(globals_dict) -> SimpleExecCtx:
    wfid = globals_dict.get("WFID")
    execid = globals_dict.get("EXECUTIONID")
    _now = datetime.utcnow().isoformat()
    now = globals_dict.get("NOW", _now)
    return SimpleExecCtx(
        wfid=wfid,
        execid=execid,
        execution_dt=now,
    )


def build_ctx(wfid, execid, now=None) -> SimpleExecCtx:
    _now = now or datetime.utcnow().isoformat()
    return SimpleExecCtx(
        wfid=wfid,
        execid=execid,
        execution_dt=_now,
    )


def _write_pickle(name, data, ctx: SimpleExecCtx):
    fpath = f"/tmp/{ctx.wfid}.{ctx.execid}.{name}.pickle"
    metapath = f"/tmp/{ctx.wfid}.{ctx.execid}.{name}.json"
    with open(fpath, "wb") as f:
        f.write(cloudpickle.dumps(data))
        logger.debug("CACHE: Wrote to %s", fpath)
    with open(metapath, "w", encoding="utf-8") as f:
        json.dump(asdict(ctx), f)


def _restore_pickle(name, ctx: SimpleExecCtx):
    fpath = f"/tmp/{ctx.wfid}.{ctx.execid}.{name}.pickle"
    metapath = f"/tmp/{ctx.wfid}.{ctx.execid}.{name}.json"
    try:
        with open(fpath, "rb") as f:
            data = cloudpickle.load(f)
            logger.debug("CACHE: Reading from %s", fpath)
        with open(metapath, "r") as f:
            data = f.read()
            meta = json.loads(data)

        return data, meta
    except EOFError:
        return None
    except FileNotFoundError:
        return None


def _write_fileserver(name, data, ctx: SimpleExecCtx):
    urlpath = f"{settings.EXT_KV_LOCAL_ROOT}/cache/{ctx.wfid}.{ctx.execid}.{name}"
    metapath = f"{settings.EXT_KV_LOCAL_ROOT}/cache/{ctx.wfid}.{ctx.execid}.{name}.json"
    blob = cloudpickle.dumps(data)
    rsp = httpx.put(urlpath, content=blob)
    rsp2 = httpx.put(metapath, json=asdict(ctx))
    if rsp.status_code > 202 and rsp2.status_code > 202:
        logger.warning("CACHE: writing to fileserver failed %s", urlpath)
    else:
        logger.debug("CACHE: wrote to fileserver %s", urlpath)


def _restore_fileserver(name, ctx: SimpleExecCtx):
    urlpath = f"{settings.EXT_KV_LOCAL_ROOT}/cache/{ctx.wfid}.{ctx.execid}.{name}"
    metapath = f"{settings.EXT_KV_LOCAL_ROOT}/cache/{ctx.wfid}.{ctx.execid}.{name}.json"
    data = None
    meta = None

    try:
        rsp = httpx.get(urlpath)
        rsp2 = httpx.get(metapath)
        if rsp.status_code == 200 and rsp2.status_code == 200:
            data = cloudpickle.loads(rsp.content)
            meta = rsp2.json()
            logger.debug("CACHE: Reading from fileserver %s", urlpath)
    except Exception as e:
        logger.warning(e)
    return data, meta


def is_valid_date(cache_dt: str, valid_for_min: int) -> bool:
    dt = datetime.fromisoformat(cache_dt)
    now = datetime.utcnow()
    elapsed = round((now - dt).seconds / 60)
    if elapsed > valid_for_min:
        return False
    return True


def cache_manager_write(data, conf: CacheConfig):
    if conf.strategy == "local" and conf.ctx.wfid:
        _write_pickle(conf.name, data, conf.ctx)
    elif conf.strategy == "fileserver" and conf.ctx.wfid:
        _write_fileserver(conf.name, data, conf.ctx)
    else:
        logger.warning("CACHE: Invalid caching strategy %s", conf.strategy)


def cache_manager_read(conf: CacheConfig):
    data = None
    meta = None
    if conf.strategy == "local" and conf.ctx.wfid:
        data, meta = _restore_pickle(conf.name, conf.ctx)
    elif conf.strategy == "fileserver" and conf.ctx.wfid:
        data, meta = _restore_fileserver(conf.name, conf.ctx)
    else:
        logger.warning("CACHE: Invalid caching strategy %s", conf.strategy)
    return data, meta


def frozen_result(
    name=None,
    wfid=None,
    execid=None,
    valid_for_min=60,
    strategy="local",
    from_global: Optional[Dict[str, Any]] = None,
):

    if not wfid and not from_global:
        raise TypeError("wfid or global should be provided")

    if from_global:
        ctx = build_ctx_global(from_global)
    else:
        ctx = build_ctx(wfid, execid)

    cache_conf = CacheConfig(
        name=name, ctx=ctx, valid_for_min=valid_for_min, strategy=strategy
    )

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_conf.name:
                cache_conf.name = func.__name__

            result, meta = cache_manager_read(cache_conf)
            valid = False
            if meta:
                valid = is_valid_date(meta["execution_dt"], valid_for_min)
            if not result or not valid:
                result = func(*args, **kwargs)
                cache_manager_write(result, cache_conf)
            return result

        return wrapper

    return decorate


if __name__ == "__main__":

    @frozen_result(wfid="test", execid="test_t", strategy="fileserver", valid_for_min=5)
    def my_func(msg):
        print(msg)
        return msg * 2

    my_func("hello world")
