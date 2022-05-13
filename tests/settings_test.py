import os
import sys

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
        "lab.client": {"level": LOGLEVEL, "handlers": ["console", "error_console"]},
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
