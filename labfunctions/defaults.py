from collections import namedtuple

# Shared defaults by server, agent and client
QueuesNS = namedtuple("QueuesNS", ["control", "machine", "build"])
Q_NS = QueuesNS(control="ctrl", machine="mch", build="bui")
CLOUD_TAG = "nbworkflows"

REFRESH_TOKEN_PATH = "auth/refresh_token"

API_VERSION = "v1"

AGENT_USER_PREFIX = "agt"
AGENT_SCOPES = "agent:rw"
AGENT_ADMIN_SCOPES = "agent:r:w,admin:r"
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
CLIENT_HOME_DIR = ".labfunctions/"
CLIENT_TIMEOUT = 60
CLIENT_CREDS_FILE = "credentials.json"
CLIENT_AGENT_CREDS_FILE = "agent.creds.json"

DOCKERFILE_MAINTENER = "NB Workflows <package@nbworkflows.com>"
DOCKERFILE_IMAGE = "nuxion/labfunctions-client"
DOCKERFILE_IMAGE_GPU = "nuxion/labfunctions-client-gpu"
DOCKER_AUTHOR = "nbworkflows"
DOCKER_UID = "1000"
DOCKER_GID = "997"

# Sanic
SANIC_APP_NAME = "labfunctions"

NB_OUTPUTS = "outputs"

EXECUTIONTASK_VAR = "NB_EXECUTION_TASK"

BASE_PATH_ENV = "NB_BASE_PATH"

PROJECT_UPLOADS = "uploads"
PROJECT_HISTORY = "history"

# see https://zelark.github.io/nano-id-cc/
PROJECT_ID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
PROJECTID_MIN_LEN = 10  # 13 years 1% collision at 100 projects creations per hour
PROJECTID_MAX_LEN = 16
WFID_LEN = 11  # ~139 thousand years 1% collision at 1000 jobs creation per hour
EXECID_LEN = 14  # ~20 years %1 collision at 1000 execs per second
PIPEID_LEN = 11
NANO_ID_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-"
NANO_URLSAFE_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz-_"
NANO_MACHINE_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"

MACHINE_TYPE = "cpu"
CLUSTER_NAME = "default"

AGENT_HOMEDIR = "/home/op"
AGENT_DOCKER_IMG = "nuxion/labfunctions"
AGENT_ENV_TPL = "agent.docker.envfile"

NVIDIA_GPG_VERSION = "2004"
NVIDIA_GPG_KEY = "3bf863cc"
