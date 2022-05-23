import functools
import ssl
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union
from urllib.parse import urlparse

from pydantic.validators import make_arbitrary_type_validator
from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.sentinel import Sentinel
from redis.exceptions import RedisError, WatchError


class SSLContext(ssl.SSLContext):
    """
    Required to avoid problems with
    """

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        yield make_arbitrary_type_validator(ssl.SSLContext)


@dataclass
class RedisSettings:
    """
    No-Op class used to hold redis connection redis_settings.
    """

    host: str = "localhost"
    port: int = 6379
    database: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: Union[bool, None, SSLContext] = None
    conn_timeout: int = 1
    conn_retries: int = 5
    conn_retry_delay: int = 1
    decode_responses: bool = True

    sentinel: bool = False
    sentinel_master: str = "mymaster"

    @classmethod
    def from_dsn(cls, dsn: str, decode_responses=True) -> "RedisSettings":
        conf = urlparse(dsn)
        assert conf.scheme in {"redis", "rediss"}, "invalid DSN scheme"
        return RedisSettings(
            host=conf.hostname or "localhost",
            port=conf.port or 6379,
            ssl=conf.scheme == "rediss",
            username=conf.username,
            password=conf.password,
            database=int((conf.path or "0").strip("/")),
            decode_responses=decode_responses,
        )

    def __repr__(self) -> str:
        return "RedisSettings({})".format(
            ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        )


def create_pool(
    dsn_url: str,
    decode_responses=True,
) -> Redis:
    """
    Create a new redis pool, retrying up to ``conn_retries`` times if the connection fails.
    Returns a :class:`arq.connections.ArqRedis` instance, thus allowing job enqueuing.
    """
    settings = RedisSettings.from_dsn(dsn_url)

    assert not (
        type(settings.host) is str and settings.sentinel
    ), "str provided for 'host' but 'sentinel' is true; list of sentinels expected"

    if settings.sentinel:

        def pool_factory(*args: Any, **kwargs: Any) -> Redis:
            client = Sentinel(
                *args, sentinels=settings.host, ssl=settings.ssl, **kwargs
            )
            return client.master_for(settings.sentinel_master)

    else:
        pool_factory = functools.partial(
            Redis,
            host=settings.host,
            port=settings.port,
            socket_connect_timeout=settings.conn_timeout,
            ssl=settings.ssl,
            decode_responses=settings.decode_responses,
        )

    pool = pool_factory(
        db=settings.database,
        username=settings.username,
        password=settings.password,
        encoding="utf8",
    )
    return pool
