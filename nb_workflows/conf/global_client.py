import os

from nb_workflows.secrets import nbvars

# WARNING:
# We do our best effort to keep sensible information private
# but in the scenario of an intrusion into the network or machines
# where agents or servers that represents a risk for the information
# stored in that machines.


# Main settings
WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://localhost:8000")
# PROJECTID = "{{ data.projectid }}"
# PROJECT_NAME = "{{ data.project_name }}"
PROJECTID = ""
PROJECT_NAME = ""

# Theese information is used to run workloads in the workers.
# Don't modify at least you know what you are doing.
AGENT_TOKEN = nbvars.get("AGENT_TOKEN", "")
AGENT_REFRESH_TOKEN = nbvars.get("AGENT_REFRESH", "")

# USER Credentials
CLIENT_TOKEN = nbvars.get("NB_CLIENT_TOKEN", "")
CLIENT_REFRESH_TOKEN = nbvars.get("NB_CLIENT_REFRESH", "")

# Log
LOGLEVEL = "INFO"
LOGFORMAT = "%(levelname)s - %(message)s"


# Folders
BASE_PATH = nbvars.get("NB_BASEPATH", os.getcwd())

# Options to build the docker image used as runtime of
# this project.
DOCKER_IMAGE = {
    "maintener": "NB Workflows <package@nbworkflows.com>",
    "image": "python:3.8.10-slim",
    # TODO:
    # Should be managed in the server
    # Would it have to be based on the id of the user?
    "user": {"uid": 1089, "gid": 1090},
    "build_packages": "build-essential libopenblas-dev git",
    "final_packages": "vim-tiny",
}

DOCKER_COMPOSE = {
    "postgres": {"image": "postgres:14-alpine", "listen_addr": "5432"},
    "redis": {"image": "redis:6-alpine", "listen_addr": "6379"},
    "web": {"listen_addr": "8000"},
    "jupyter": {"listen_addr": "127.0.0.1:8888"},
}
