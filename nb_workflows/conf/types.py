from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseSettings

from nb_workflows.utils import Singleton


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
    SERVER_DATA_FOLDER: str
    WORKER_DATA_FOLDER: str
    NB_WORKFLOWS: str
    NB_OUTPUT: str
    NB_PROJECTS: str
    WF_UPLOADS: str
    DOCKER_RUNTIMES: str

    WEB_REDIS: Optional[str] = None
    RQ_REDIS_HOST: Optional[str] = None
    RQ_REDIS_PORT: Optional[str] = None
    RQ_REDIS_DB: Optional[str] = None
    RQ_CONTROL_QUEUE: str = "control"
    EXECUTIONID_LEN: int = 8
    PROJECTID_LEN: int = 10

    # Logs:
    LOGLEVEL: str = "INFO"
    LOGFORMAT: str = "%(asctime)s %(message)s"
    DEBUG: bool = False

    FILESERVER: Optional[str] = None
    FILESERVER_BUCKET: Optional[str] = None
    SETTINGS_MODULE: Optional[str] = None

    def rq2dict(self):
        return dict(
            host=self.RQ_REDIS_HOST,
            port=int(self.RQ_REDIS_PORT),
            db=int(self.RQ_REDIS_DB),
        )

    class Config:
        env_prefix = "NB_"


class ClientSettings(BaseSettings):
    WORKFLOW_SERVICE: str
    PROJECTID: str

    AGENT_TOKEN: str
    AGENT_REFRESH_TOKEN: str

    BASE_PATH: str
    # NB_WORKFLOWS: str
    # NB_OUTPUT: str
    LOGLEVEL: str = "INFO"
    LOGFORMAT: str = "%(asctime)s %(message)s"
    DEBUG: bool = False

    PROJECT_NAME: Optional[str] = None
    PROJECTID_LEN: int = 10
    CLIENT_TOKEN: Optional[str] = None
    CLIENT_REFRESH_TOKEN: Optional[str] = None
    VERSION: Optional[str] = "0.1.0"
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL_OK: Optional[str] = None
    SLACK_CHANNEL_FAIL: Optional[str] = None
    DISCORD_OK: Optional[str] = None
    DISCORD_FAIL: Optional[str] = None

    FILESERVER: Optional[str] = None
    SETTINGS_MODULE: Optional[str] = None
    DOCKER_IMAGE: Dict[str, Any] = None
    DOCKER_COMPOSE: Dict[str, Any] = None

    class Config:
        env_prefix = "NB_"
