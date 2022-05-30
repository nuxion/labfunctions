from typing import Any, Dict, List, Optional

from pydantic import BaseModel, BaseSettings, RedisDsn

from labfunctions.defaults import (
    EXECID_LEN,
    LABFILE_NAME,
    PROJECTID_MIN_LEN,
    SERVICE_URL,
    WFID_LEN,
)


class ConfigCliType(BaseModel):
    """Config for default values for cli"""

    url_service: str = SERVICE_URL
    lab_file: Optional[str] = LABFILE_NAME


class SecuritySettings(BaseSettings):
    JWT_PUBLIC: str
    JWT_PRIVATE: str
    JWT_ALG: str = "ES512"
    JWT_EXP: int = 30  # 30 minutes
    JWT_REQUIRES_CLAIMS: List[str] = ["exp"]
    JWT_SECRET: Optional[str] = None
    JWT_ISS: Optional[str] = None
    JWT_AUD: Optional[str] = None
    REFRESH_TOKEN_TTL: int = 3600 * 168  # 7 days
    TOKEN_STORE_URL: Optional[str] = None
    AUTH_SALT: str = "changeit"
    AUTH_ALLOW_REFRESH: bool = True
    AUTH_CLASS = "labfunctions.security.authentication.Auth"
    AUTH_FUNCTION = "labfunctions.managers.users_mg.authenticate"

    class Config:
        env_prefix = "LF_"


class ServerSettings(BaseSettings):
    # Security
    AGENT_TOKEN: str
    AGENT_REFRESH_TOKEN: str

    # Services
    WORKFLOW_SERVICE: str
    SQL: str
    ASQL: str
    AGENT_TOKEN_EXP: int = (60 * 60) * 12

    # Folders:
    BASE_PATH: str
    DOCKER_REGISTRY: Optional[str] = None

    SECURITY: Optional[SecuritySettings] = None

    DEV_MODE: bool = False
    WEB_REDIS: Optional[RedisDsn] = None
    QUEUE_REDIS: Optional[RedisDsn] = None
    QUEUE_DEFAULT_TIMEOUT: str = "30m"
    CONTROL_QUEUE: str = "default.control"
    BUILD_QUEUE: str = "default.build"

    # ids generations
    EXECID_LEN: int = EXECID_LEN
    PROJECTID_LEN: int = PROJECTID_MIN_LEN
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
    CLUSTER_SPEC: str = "scripts/local_clusters.yaml"
    AGENT_HOMEDIR: str = "/home/op"
    AGENT_ENV_FILE: str = ".env.dev.docker"
    AGENT_HEARTBEAT_CHECK: int = 60 * 5
    AGENT_HEARTBEAT_TTL: int = 80 * 3

    # Logs:
    LOGLEVEL: str = "INFO"
    LOGCONFIG: Dict[str, Any] = {}
    DEBUG: bool = False

    PROJECTS_STORE_CLASS_ASYNC = "labfunctions.io.kv_local.AsyncKVLocal"
    PROJECTS_STORE_CLASS_SYNC = "labfunctions.io.kv_local.KVLocal"
    PROJECTS_STORE_BUCKET = "labfunctions"
    EXT_KV_LOCAL_ROOT: Optional[str] = None
    EXT_KV_FILE_URL: Optional[str] = None

    SETTINGS_MODULE: Optional[str] = None
    DNS_IP_ADDRESS: str = "8.8.8.8"

    class Config:
        env_prefix = "LF_"


class ClientSettings(BaseSettings):
    WORKFLOW_SERVICE: str
    PROJECTID: str

    BASE_PATH: str
    LOGLEVEL: str = "INFO"
    LOGCONFIG: Dict[str, Any] = {}
    DEBUG: bool = False
    LOCAL: bool = False
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

    PROJECTS_STORE_CLASS = "labfunctions.io.kv_local.KVLocal"
    PROJECTS_STORE_BUCKET = "labfunctions"
    EXT_KV_LOCAL_ROOT: Optional[str] = None
    EXT_KV_FILE_URL: Optional[str] = None

    SETTINGS_MODULE: Optional[str] = None
    # DOCKER_COMPOSE: Dict[str, Any] = None

    class Config:
        env_prefix = "LF_"
