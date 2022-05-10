import logging
from enum import Enum

# from warnings import warn


class Colors(str, Enum):  # no cov
    END = "\033[0m"
    BLUE = "\033[01;34m"
    GREEN = "\033[01;32m"
    YELLOW = "\033[01;33m"
    RED = "\033[01;31m"


srv_logger = logging.getLogger("nbwork.server")  # no cov
"""
General Server logger
"""

error_logger = logging.getLogger("nbwork.error")  # no cov
"""
Logger used for errors
"""

c_logger = logging.getLogger("nbwork.agent")  # no cov
"""
Logger used by the client
"""
