import os

# detailed_format = "[%(asctime)s] - %(name)s %(lineno)d - %(levelname)s - %(message)s"
detailed_format = "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s"

# SALT is used as salt hash for users passwords
SALT = os.getenv("SALT", "changeme")
# Signing data
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")

AGENT_TOKEN = os.getenv("NB_AGENT_TOKEN", "changeme")
AGENT_REFRESH_TOKEN = os.getenv("NB_AGENT_REFRESH_TOKEN", "changeme")

AGENT_TOKEN_EXP = (60 * 60) * 12
# Services
SQL = os.getenv("NB_SQL", "postgresql://postgres:secret@postgres:5432/nb_workflows")
ASQL = os.getenv(
    "NB_ASQL", "postgresql+asyncpg://postgres:secret@postgres:5432/nb_workflows"
)
FILESERVER = os.getenv("NB_FILESERVER")
FILESERVER_BUCKET = "nbwf"

# RQ_REDIS_HOST = os.getenv("NB_RQ_HOST", "redis")
# RQ_REDIS_PORT = os.getenv("NB_RQ_PORT", "6379")
# RQ_REDIS_DB = os.getenv("NB_RQ_DB", "2")
# WEB_REDIS = os.getenv("NB_WEB_REDIS", "redis://redis:6379/2")


WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://localhost:8000")
# Logs
LOGFORMAT = detailed_format

# General Folders for the server
BASE_PATH = os.getenv("NB_BASEPATH", os.getcwd())
SERVER_DATA_FOLDER = ".server_data/"
WORKER_DATA_FOLDER = ".worker_data/"

NB_WORKFLOWS = os.getenv("NB_WORKFLOWS", "workflows/")
NB_OUTPUT = os.getenv("NB_NB_OUTPUT", "outputs/")
NB_PROJECTS = "projects"
DOCKER_RUNTIMES = "runtimes/"
