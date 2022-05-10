from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Generator, Union

from labfunctions.utils import get_class


class KeyReadError(Exception):
    def __init__(self, bucket, key, error_msg):
        msg = f"Value not found for key {key} in {bucket} with error: {error_msg}"
        super().__init__(msg)


class KeyWriteError(Exception):
    def __init__(self, bucket, key, error_msg):
        msg = f"Value not written for key {key} in {bucket} with error: {error_msg}"
        super().__init__(msg)


class GenericKVSpec(ABC):
    """
    This is a generic KV store mostly use for project data related
    The interface is very simple allowing the common put/get actions
    either loading data in memory or streaming data for big files

    For examples about how to use some of them see tests/test_io_kv.py

    This interface is offered in a sync and async version
    """

    def __init__(self, bucket: str, client_opts: Dict[str, Any] = {}):
        self._opts = client_opts
        self._bucket = bucket

    @abstractmethod
    def put(self, key: str, bdata: bytes):
        pass

    @abstractmethod
    def put_stream(self, key: str, generator: Generator[bytes, None, None]) -> bool:
        pass

    @abstractmethod
    def get(self, key: str) -> Union[bytes, str, None]:
        pass

    @abstractmethod
    def get_stream(self, key: str) -> Generator[bytes, None, None]:
        pass

    @staticmethod
    def create(store_class, bucket, opts: Dict[str, Any] = {}) -> "GenericKVSpec":
        Class = get_class(store_class)
        return Class(bucket, opts)


class AsyncKVSpec(ABC):
    """
    This is a generic KV store mostly use for project data related
    The interface is very simple allowing the common put/get actions
    either loading data in memory or streaming data for big files

    For examples about how to use some of them see tests/test_io_kv.py


    This interface is offered in a sync and async version
    """

    def __init__(self, client_opts: Dict[str, Any], bucket: str):
        self._opts = client_opts
        self._bucket = bucket

    @abstractmethod
    async def put(self, key: str, bdata: bytes):
        pass

    @abstractmethod
    async def put_stream(
        self, key: str, generator: Generator[bytes, None, None]
    ) -> bool:
        pass

    @abstractmethod
    async def get(self, key: str) -> Union[bytes, str, None]:
        pass

    @abstractmethod
    async def get_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        pass

    @staticmethod
    def create(store_class, bucket, opts: Dict[str, Any] = {}) -> "GenericKVSpec":
        Class = get_class(store_class)
        return Class(bucket, opts)
