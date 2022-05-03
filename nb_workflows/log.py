import logging
import sys
from enum import Enum
from typing import Any, Dict

# from warnings import warn

LOGGING_CONFIG_DEFAULTS: Dict[str, Any] = dict(  # no cov
    version=1,
    disable_existing_loggers=False,
    loggers={
        "nbwork.server": {"level": "INFO", "handlers": ["console"]},
        "nbwork.error": {
            "level": "INFO",
            "handlers": ["error_console"],
            "propagate": True,
            "qualname": "nbwork.error",
        },
        "nbwork.agent": {
            "level": "INFO",
            "handlers": ["agent_console"],
            "propagate": True,
            "qualname": "nbwork.agent",
        },
    },
    handlers={
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stdout,
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stderr,
        },
        "agent_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": sys.stdout,
        },
    },
    formatters={
        "generic": {
            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "access": {
            "format": "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
            + "%(request)s %(message)s %(status)d %(byte)d",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
)


class Colors(str, Enum):  # no cov
    END = "\033[0m"
    BLUE = "\033[01;34m"
    GREEN = "\033[01;32m"
    YELLOW = "\033[01;33m"
    RED = "\033[01;31m"


logger = logging.getLogger("nbwork.server")  # no cov
"""
General Server logger
"""

error_logger = logging.getLogger("sanic.error")  # no cov
"""
Logger used for errors
"""

agent_logger = logging.getLogger("nbwork.agent")  # no cov
"""
Logger used by agent for info loggin
"""
