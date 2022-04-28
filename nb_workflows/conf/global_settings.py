import os

# detailed_format = "[%(asctime)s] - %(name)s %(lineno)d - %(levelname)s - %(message)s"
detailed_format = "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s"

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

WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://localhost:8000")
# Logs
LOGFORMAT = detailed_format

# General Folders for the server
BASE_PATH = os.getenv("NB_BASEPATH", os.getcwd())
AGENT_DATA_FOLDER = ".worker_data/"
SECURITY = {
    "JWT_ALG": "ES512",
    "JWT_EXP": 30,
    "AUTH_CLASS": "nb_workflows.security.authentication.Auth",
    "AUTH_FUNCTION": "nb_workflows.managers.users_mg.authenticate",
}

NB_WORKFLOWS = os.getenv("NB_WORKFLOWS", "workflows/")
NB_OUTPUT = os.getenv("NB_NB_OUTPUT", "outputs/")
