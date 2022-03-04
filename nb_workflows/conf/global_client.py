import os

# Main settings
WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://localhost:8000")

PROJECTID = ""
PROJECT_NAME = ""

CLIENT_TOKEN = os.getenv("NB_CLIENT_TOKEN")
CLIENT_REFRESH_TOKEN = os.getenv("NB_CLIENT_REFRESH")

# Log
LOGLEVEL = os.getenv("NB_LOG", "INFO")
# None should be false, anything else true
DEBUG = bool(os.getenv("NB_DEBUG", None))


# Folders
BASE_PATH = os.getenv("NB_BASEPATH", os.getcwd())

# Options to build the docker image used as runtime of this
# this project.
DOCKER_IMAGE = {
    "maintener": "NB Workflows <package@nbworkflows.com>",
    "image": "python:3.8.10-slim",
    # TODO:
    # Should be managed server side
    # Would it have to be based on the id of the user?
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
