from sanic import Sanic
from sanic_jwt import initialize as sanic_initialize

from nb_workflows.conf import settings

from .authenticate import NBAuthentication


def initialize() -> NBAuthentication:
    """To be used out of the webserver context"""
    app = Sanic("nb_workflows")
    a = sanic_initialize(
        app,
        authentication_class=NBAuthentication,
        secret=settings.SECRET_KEY,
        refresh_token_enabled=True,
    )
    return app.ctx.auth


def get_auth() -> NBAuthentication:
    """to get a NBAuthentication instance from
    webserver cxt"""
    current = Sanic.get_app("nb_workflows")
    return current.ctx.auth
