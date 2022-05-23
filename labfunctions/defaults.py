# Shared defaults by server, agent and client
CLOUD_TAG = "lab"
ENV_PREFIX = "LF_"
LABFILE_VER = "0.3"
LABFILE_NAME = "labfile.yaml"


REFRESH_TOKEN_PATH = "auth/refresh_token"

API_VERSION = "v1"
SERVICE_URL = "http://localhost:8000"
SERVICE_URL_ENV = "LF_WORKFLOW_SERVICE"

AGENT_USER_PREFIX = "agt"
AGENT_SCOPES = "agent:rw"
AGENT_ADMIN_SCOPES = "agent:r:w,admin:r"
AGENT_LEN = 8
AGENT_TOKEN_ENV = "LF_AGENT_TOKEN"
AGENT_REFRESH_ENV = "LF_AGENT_REFRESH_TOKEN"

NOTEBOOKS_DIR = "notebooks/"

# Builder
ZIP_GIT_PREFIX = "src/"

# Secrets and security
SECRETS_FILENAME = ".secrets"
NBVARS_VAR_NAME = "LF_LABVARS"
NBVARS_FILENAME = "local.nbvars"
PRIVKEY_VAR_NAME = "PRIVATE_KEY"

# Client DEFAULT OPTIONS
CLIENT_TMP_FOLDER = ".nb_tmp"
CLIENT_HOME_DIR = ".labfunctions/"
CLIENT_TIMEOUT = 60
CLIENT_CREDS_FILE = "credentials.json"
CLIENT_AGENT_CREDS_FILE = "agent.creds.json"
CLIENT_CONFIG_CLI = "config.toml"

DOCKERFILE_MAINTENER = "LabFunctions <package@labscalar.com>"
DOCKERFILE_IMAGE = "nuxion/labfunctions"
DOCKER_AUTHOR = "labfunctions"
DOCKER_UID = "1000"
DOCKER_GID = "997"
DOCKER_APP_UID = 1089
DOCKER_APP_GID = 1090

# Sanic
SANIC_APP_NAME = "labfunctions"

NB_OUTPUTS = "outputs"

EXECUTIONTASK_VAR = "LF_EXECUTION_TASK"
JUPYTERCTX_VAR = "LF_JUPYTER_CTX"

BASE_PATH_ENV = "LF_BASE_PATH"

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
DOCKER_CUDA_VER = "11.6"

SERVER_LOG = "lab.server"
ERROR_LOG = "lab.error"
CLIENT_LOG = "lab.client"
CONTROL_QUEUE = "default.control"
BUILD_QUEUE = "default.build"
