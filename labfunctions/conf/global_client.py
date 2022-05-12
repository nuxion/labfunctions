import os
import sys

from labfunctions import defaults

# WARNING:
# We do our best effort to keep sensible information private
# but in the scenario of an intrusion into the network or machines
# where agents or servers that represents a risk for the information
# stored in that machines.


# Main settings
PROJECTID = ""
PROJECT_NAME = ""
# Theese information is used to run workloads in the workers.
# Don't modify at least you know what you are doing.
# Log
LOGLEVEL = "WARNING"
LOGCONFIG = dict(  # no cov
    version=1,
    disable_existing_loggers=False,
    loggers={
        defaults.CLIENT_LOG: {
            "level": LOGLEVEL,
            "handlers": ["console", "error_console"],
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
    },
    formatters={
        "generic": {
            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
)
