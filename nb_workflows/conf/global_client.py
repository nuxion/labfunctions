import os

# WARNING:
# We do our best effort to keep sensible information private
# but in the scenario of an intrusion into the network or machines
# where agents or servers that represents a risk for the information
# stored in that machines.


# Main settings
PROJECTID = ""
PROJECT_NAME = ""

WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://localhost:8000")

# Theese information is used to run workloads in the workers.
# Don't modify at least you know what you are doing.
# Log
detailed_format = "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s"
LOGLEVEL = "INFO"
# LOGFORMAT = "%(levelname)s - %(message)s"
LOGFORMAT = detailed_format


# DOCKER_COMPOSE = {
#     "postgres": {"image": "postgres:14-alpine", "listen_addr": "5432"},
#     "redis": {"image": "redis:6-alpine", "listen_addr": "6379"},
#     "web": {"listen_addr": "8000"},
#     "jupyter": {"listen_addr": "127.0.0.1:8888"},
# }
