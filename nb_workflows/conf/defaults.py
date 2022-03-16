from collections import namedtuple

# Shared defaults by server, agent and client
QueuesNS = namedtuple("QueuesNS", ["control", "machine", "build"])
Q_NS = QueuesNS(control="ctrl", machine="mch", build="bui")


# Builder
ZIP_GIT_PREFIX = "src/"

# Secrets and security
SECRETS_FILENAME = ".secrets"
NBVARS_VAR_NAME = "NBVARS"
PRIVKEY_VAR_NAME = "PRIVATE_KEY"

# Folders name
CLIENT_TMP_FOLDER = ".nb_tmp"

DOCKERFILE_RUNTIME_NAME = "Dockerfile.nbruntime"


# Sanic
SANIC_APP_NAME = "nb_workflows"

WORKFLOWS_FOLDER_NAME = "workflows"

NB_OUTPUTS = "outputs"

EXECUTIONTASK_VAR = "NB_EXECUTION_TASK"

BASE_PATH_ENV = "NB_BASE_PATH"

# see https://zelark.github.io/nano-id-cc/
PROJECTID_LEN = 8  # 3 years 1% collision at 100 projects creations per hour
JOBID_LEN = 11  # ~139 thousand years 1% collision at 1000 jobs creation per hour
EXECID_LEN = 14  # ~20 years %1 collision at 1000 execs per second
PIPEID_LEN = 11
NANO_ID_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-"
