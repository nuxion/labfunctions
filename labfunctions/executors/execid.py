from collections import namedtuple
from typing import List, NamedTuple

from labfunctions import defaults
from labfunctions.hashes import generate_random


class FirmsTypes(NamedTuple):
    start: str = "0"
    build: str = "bld"
    dispatcher: str = "dsp"
    docker: str = "dck"
    web: str = "web"
    local: str = "loc"
    machine: str = "mch"


class ExecID:

    types = FirmsTypes()

    def __init__(self, execid=None, size=defaults.EXECID_LEN, prefix=None):
        """A general class with manage executions id for different queues in RQ"""
        self._id = execid or generate_random(size=size)
        if prefix:
            self._id = f"{prefix}{self._id}"

    def firm_by_type(self, firm_type) -> str:
        """it will look at self.types to find the sign"""
        _firm = getattr(self.types, firm_type)
        self.firm_with(_firm)
        return self._id

    def firm_with(self, firm) -> str:
        """it should prepend the word"""
        self._id = f"{firm}.{self._id}"
        return self._id

    def pure(self) -> str:
        pure = self._id
        if "." in self._id:
            pure = self._id.rsplit(".", maxsplit=1)[1]
        return pure

    @property
    def id(self):
        return self._id

    def __str__(self):
        return self._id

    def __repr__(self):
        return self._id
