import logging
from enum import Enum

from labfunctions import defaults

# from warnings import warn


class Colors(str, Enum):  # no cov
    END = "\033[0m"
    BLUE = "\033[01;34m"
    GREEN = "\033[01;32m"
    YELLOW = "\033[01;33m"
    RED = "\033[01;31m"


server_logger = logging.getLogger(defaults.SERVER_LOG)  # no cov
"""
General Server logger
"""

error_logger = logging.getLogger(defaults.ERROR_LOG)  # no cov
"""
Logger used for errors
"""

client_logger = logging.getLogger(defaults.CLIENT_LOG)  # no cov
"""
Logger used by the client
"""
