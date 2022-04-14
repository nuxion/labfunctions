from typing import Any, Dict, Optional

from pydantic import BaseSettings, RedisDsn

from nb_workflows.defaults import EXECID_LEN, PROJECTID_LEN, WFID_LEN


class ServerSettings(BaseSettings):
    # Security
    SALT: str
    SECRET_KEY: str
    AGENT_TOKEN: str
    AGENT_REFRESH_TOKEN: str
    AGENT_TOKEN_EXP: int

    # Services
    SQL: str
    ASQL: str
    WORKFLOW_SERVICE: str

    # Folders:
    BASE_PATH: str
    NB_WORKFLOWS: str
    NB_OUTPUT: str
    DOCKER_REGISTRY: Optional[str] = None

    DEV_MODE: bool = False
    WEB_REDIS: Optional[RedisDsn] = None
    RQ_REDIS: Optional[RedisDsn] = None
    RQ_CONTROL_QUEUE: str = "control"

    # ids generations
    EXECID_LEN: int = EXECID_LEN
    PROJECTID_LEN: int = PROJECTID_LEN
    WFID_LEN: int = WFID_LEN

    # eventes
    EVENTS_BLOCK_MS: int = 10 * 1000
    EVENTS_STREAM_TTL_SECS: int = 60 * 60

    # docker
    DOCKER_UID: str = "1000"
    DOCKER_GID: str = "997"

    # cluster
    AGENT_DATA_FOLDER: str = ".worker_data/"
    CLUSTER_SSH_KEY_USER: str = "op"
    CLUSTER_SSH_PUBLIC_KEY: Optional[str] = None
    AGENT_HOMEDIR: str = "/home/op"
    AGENT_ENV_FILE: str = ".env.dev.docker"
    AGENT_HEARTBEAT_CHECK: int = 60 * 5
    AGENT_HEARTBEAT_TTL: int = 80 * 3

    # Logs:
    LOGLEVEL: str = "INFO"
    LOGFORMAT: str = "%(asctime)s %(message)s"
    DEBUG: bool = False

    FILESERVER: Optional[str] = None
    FILESERVER_BUCKET: Optional[str] = None
    SETTINGS_MODULE: Optional[str] = None
    DNS_IP_ADDRESS: str = "8.8.8.8"

    class Config:
        env_prefix = "NB_"


class ClientSettings(BaseSettings):
    WORKFLOW_SERVICE: str
    PROJECTID: str

    BASE_PATH: str
    # NB_WORKFLOWS: str
    # NB_OUTPUT: str
    LOGLEVEL: str = "INFO"
    LOGFORMAT: str = "%(asctime)s %(message)s"
    DEBUG: bool = False
    NBVARS: Optional[str] = None
    AGENT_TOKEN: Optional[str] = None
    AGENT_REFRESH_TOKEN: Optional[str] = None

    PROJECT_NAME: Optional[str] = None
    PROJECTID_LEN: int = 10
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL_OK: Optional[str] = None
    SLACK_CHANNEL_FAIL: Optional[str] = None
    DISCORD_OK: Optional[str] = None
    DISCORD_FAIL: Optional[str] = None

    FILESERVER: Optional[str] = None
    SETTINGS_MODULE: Optional[str] = None
    # DOCKER_COMPOSE: Dict[str, Any] = None

    class Config:
        env_prefix = "NB_"
