import os
import sys

AGENT_TOKEN_EXP = (60 * 60) * 12
# Services
SQL = os.getenv("NB_SQL", "sqlite:///db.sqlite")
ASQL = os.getenv("NB_ASQL", "sqlite+aiosqlite:///db.sqlite")
WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://localhost:8000")

# General Folders for the server
BASE_PATH = os.getenv("NB_BASEPATH", os.getcwd())
AGENT_DATA_FOLDER = ".worker_data/"
SECURITY = {
    "JWT_ALG": "ES512",
    "JWT_EXP": 30,
    "AUTH_CLASS": "labfunctions.security.authentication.Auth",
    "AUTH_FUNCTION": "labfunctions.managers.users_mg.authenticate",
}

# Logs
LOGLEVEL = "INFO"
LOGCONFIG = dict(  # no cov
    version=1,
    disable_existing_loggers=False,
    loggers={
        "nbwork.server": {"level": LOGLEVEL, "handlers": ["console"]},
        "nbwork.error": {
            "level": LOGLEVEL,
            "handlers": ["error_console"],
            "propagate": True,
            "qualname": "nbwork.error",
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
