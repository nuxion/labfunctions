import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Settings:
    SALT: str
    SECRET_KEY: str
    CLIENT_TOKEN: str
    # Services
    SQL: str
    ASQL: str

    RQ_REDIS_HOST: str
    RQ_REDIS_PORT: str
    RQ_REDIS_DB: str

    WORKFLOW_SERVICE: str

    # MISC
    LOGLEVEL: str
    DEBUG: bool
    BASE_PATH: str
    NB_WORKFLOWS: str
    NB_OUTPUT: str

    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL_OK: Optional[str] = None
    SLACK_CHANNEL_FAIL: Optional[str] = None
    DISCORD_OK: Optional[str] = None
    DISCORD_FAIL: Optional[str] = None

    FILESERVER: Optional[str] = None
    SETTINGS_MODULE: Optional[str] = None
    DOCKER_OPTIONS: Dict[str, Any] = None
    DOCKER_COMPOSE: Dict[str, Any] = None

    def rq2dict(self):
        return dict(
            host=self.RQ_REDIS_HOST,
            port=int(self.RQ_REDIS_PORT),
            db=int(self.RQ_REDIS_DB),
        )


