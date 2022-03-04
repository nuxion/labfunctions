from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ServerSettings:
    # Security
    SALT: str
    SECRET_KEY: str
    CLIENT_TOKEN: str
    # Services
    SQL: str
    ASQL: str
    RQ_REDIS_HOST: str
    RQ_REDIS_PORT: str
    RQ_REDIS_DB: str
    WEB_REDIS: str
    WORKFLOW_SERVICE: str

    # Logs:
    LOGLEVEL: str
    DEBUG: bool

    # Folders:
    BASE_PATH: str
    SERVER_DATA_FOLDER: str
    WORKER_DATA_FOLDER: str
    NB_WORKFLOWS: str
    NB_OUTPUT: str
    NB_PROJECTS: str
    WF_UPLOADS: str
    DOCKER_RUNTIMES: str

    RQ_CONTROL_QUEUE: str = "control"
    PROJECTID_LEN: int = 10
    CLIENT_REFRESH_TOKEN: str = None

    FILESERVER: Optional[str] = None
    FILESERVER_BUCKET: Optional[str] = None
    SETTINGS_MODULE: Optional[str] = None

    def rq2dict(self):
        return dict(
            host=self.RQ_REDIS_HOST,
            port=int(self.RQ_REDIS_PORT),
            db=int(self.RQ_REDIS_DB),
        )


@dataclass
class ClientSettings:
    WORKFLOW_SERVICE: str
    PROJECTID: str

    LOGLEVEL: str
    DEBUG: bool
    BASE_PATH: str
    # NB_WORKFLOWS: str
    # NB_OUTPUT: str
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
