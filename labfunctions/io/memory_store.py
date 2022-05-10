from labfunctions.utils import Singleton


class MemoryStore(dict, metaclass=Singleton):
    """A simple wrapper around a python dict to use
    as a memory store.
    """

    pass
