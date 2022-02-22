import logging
import os
from logging import NullHandler


class Config:

    SALT = os.getenv("SALT")
    SECRET_KEY = os.getenv("SECRET_KEY")
    CLIENT_TOKEN = os.getenv("NB_TOKEN")
    # Services
    SQL = os.getenv("NB_SQL")
    ASQL = os.getenv("NB_ASQL")
    FILESERVER = os.getenv("NB_FILESERVER")

    DISCORD_EVENTS = os.getenv("DISCORD_EVENTS")
    DISCORD_ERRORS = os.getenv("DISCORD_ERRORS")

    RQ_REDIS_HOST = os.getenv("NB_RQ_HOST", "localhost")
    RQ_REDIS_PORT = os.getenv("NB_RQ_PORT", "6379")
    RQ_REDIS_DB = os.getenv("NB_RQ_DB", "2")

    WEB_REDIS = os.getenv("NB_WEB_REDIS", "redis://localhost:6379/0")
    WORKFLOW_SERVICE = os.getenv("NB_WORKFLOW_SERVICE", "http://127.0.0.1:8000")
    # MISC
    LOGLEVEL = os.getenv("NB_LOG", "INFO")
    # None should be false, anything else true
    DEBUG = bool(os.getenv("NB_DEBUG", None))

    # Folders
    BASE_PATH = os.getenv("NB_BASEPATH")
    MODELS_PATH = os.getenv("NB_MODELS")

    NB_WORKFLOWS = os.getenv("NB_WORKFLOWS", "workflows/")
    NB_OUTPUT = os.getenv("NB_NB_OUTPUT", "outputs/")

    @classmethod
    def rq2dict(cls):
        return dict(
            host=cls.RQ_REDIS_HOST,
            port=int(cls.RQ_REDIS_PORT),
            db=int(cls.RQ_REDIS_DB),
        )

    # @classmethod
    # def url_redis2dict(cls):
    #    url = cls.URL_REDIS.split("redis://")[1]
    #    h, port_db = url.split(":")
    #    p, db = port_db.split("/")

    #    return dict(
    #        host=h,
    #        port=p,
    #        db=db,
    #    )


# _LOG_LEVEl = os.getenv("NB_LOG", "INFO")
# _level = getattr(logging, Config.LOGLEVEL)
# logging.basicConfig(format='%(asctime)s %(message)s', level=_level)
logging.basicConfig(format="%(asctime)s %(message)s")
logging.getLogger(__name__).addHandler(NullHandler())
