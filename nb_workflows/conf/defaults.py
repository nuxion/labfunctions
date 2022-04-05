from collections import namedtuple

# Shared defaults by server, agent and client
QueuesNS = namedtuple("QueuesNS", ["control", "machine", "build"])
Q_NS = QueuesNS(control="ctrl", machine="mch", build="bui")

REFRESH_TOKEN_PATH = "/auth/refresh"

API_VERSION = "v1"

AGENT_USER_PREFIX = "agt"
AGENT_SCOPES = "agent:rw"
AGENT_LEN = 8

NOTEBOOKS_DIR = "notebooks/"

# Builder
ZIP_GIT_PREFIX = "src/"

# Secrets and security
SECRETS_FILENAME = ".secrets"
NBVARS_VAR_NAME = "NB_NBVARS"
NBVARS_FILENAME = "local.nbvars"
PRIVKEY_VAR_NAME = "PRIVATE_KEY"

# Client DEFAULT OPTIONS
CLIENT_TMP_FOLDER = ".nb_tmp"
CLIENT_HOME_DIR = ".nb_workflows/"
CLIENT_TIMEOUT = 60

DOCKERFILE_RUNTIME_NAME = "Dockerfile.nbruntime"
DOCKERFILE_MAINTENER = "NB Workflows <package@nbworkflows.com>"
DOCKERFILE_IMAGE = "python:3.8.10-slim"

# Sanic
SANIC_APP_NAME = "nb_workflows"

NB_OUTPUTS = "outputs"

EXECUTIONTASK_VAR = "NB_EXECUTION_TASK"

BASE_PATH_ENV = "NB_BASE_PATH"

# see https://zelark.github.io/nano-id-cc/
PROJECTID_LEN = 8  # 3 years 1% collision at 100 projects creations per hour
WFID_LEN = 11  # ~139 thousand years 1% collision at 1000 jobs creation per hour
EXECID_LEN = 14  # ~20 years %1 collision at 1000 execs per second
PIPEID_LEN = 11
NANO_ID_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-"

DOCKER_AUTHOR = "nbworkflows"
