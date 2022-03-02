import os

WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://localhost:8000")

CLIENT_TOKEN = os.getenv("NB_CLIENT_TOKEN")
CLIENT_REFRESH_TOKEN = os.getenv("NB_CLIENT_REFRESH")

# MISC
LOGLEVEL = os.getenv("NB_LOG", "INFO")
# None should be false, anything else true
DEBUG = bool(os.getenv("NB_DEBUG", None))


# Folders
BASE_PATH = os.getenv("NB_BASEPATH", os.getcwd())

NB_WORKFLOWS = os.getenv("NB_WORKFLOWS", "workflows/")
NB_OUTPUT = os.getenv("NB_NB_OUTPUT", "outputs/")

DOCKER_OPTIONS = {
    "maintener": "NB Workflows <package@nbworkflows.com>",
    "image": "python:3.8.10-slim",
    "user": {"uid": 1089, "gid": 1090},
    "build_packages": "build-essential libopenblas-dev git",
    "final_packages": "vim-tiny"
}

DOCKER_COMPOSE = {
    "postgres": {
        "image": "postgres:14-alpine",
        "listen_addr": "5432"
    },
    "redis": {
        "image": "redis:6-alpine",
        "listen_addr": "6379"
    },
    "web": {
        "listen_addr": "8000"
    },
    "jupyter": {
        "listen_addr": "127.0.0.1:8888"
    }
}
