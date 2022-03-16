import warnings

from sanic import Sanic
from sanic.response import json
from sanic_jwt import Authentication, Initialize, exceptions
from sanic_jwt import initialize as sanic_initialize
from sanic_jwt import utils

from nb_workflows.auth.types import UserData
from nb_workflows.auth.users import (
    get_user_async,
    get_userid_async,
    verify_user_from_model,
)
from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings


class NBAuthentication(Authentication):
    """https://github.com/ahopkins/sanic-jwt/blob/717f21ea3bec9338d1d3b74ef57af486d3fcaee5/example/custom_authentication_cls.py"""

    async def authenticate(self, request, *args, **kwargs):
        u = request.json.get("username", None)
        p = request.json.get("password", None)
        session = request.ctx.session
        if not u or not p:
            raise exceptions.AuthenticationFailed("Auth error")

        async with session.begin():
            user = await get_user_async(session, u)
            if user is None:
                raise exceptions.AuthenticationFailed("Auth error")

            is_valid = verify_user_from_model(user, p)
            if not is_valid:
                raise exceptions.AuthenticationFailed("Auth error")
            user_ = user.to_dict()
            user_["user_id"] = user_["id"]
            return user_

    async def store_refresh_token(self, user_id, refresh_token, *args, **kwargs):
        redis = kwargs["request"].ctx.web_redis
        key = f"nb.rtkn.{user_id}"
        # _key = await redis.get(key)
        # if not _key:
        await redis.set(key, refresh_token)

    async def retrieve_refresh_token(self, request, user_id, *args, **kwargs):
        redis = request.ctx.web_redis
        key = f"nb.rtkn.{user_id}"
        return await redis.get(key)

    async def retrieve_user(self, request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("user_id", None)
            session = request.ctx.session
            # async with session.begin():
            user = await get_userid_async(session, user_id)
            user_dict = user.to_dict(rules=("-id", "-created_at", "-updated_at"))
            user_dict["user_id"] = user_id
            return UserData(**user_dict)
        else:
            return None

    async def generate_refresh_token(self, request, user):
        """
        Generate a refresh token for a given user.
        TODO: this is temporally
        """
        warnings.warn("Refresh token never expires")

        redis = request.ctx.web_redis
        refresh_token = await redis.get(f"nb.rtkn.{user['user_id']}")
        if not refresh_token:
            refresh_token = await utils.call(self.config.generate_refresh_token())
        user_id = await self._get_user_id(user)
        await utils.call(
            self.store_refresh_token,
            user_id=user_id,
            refresh_token=refresh_token,
            request=request,
        )
        return refresh_token


def initialize(name=defaults.SANIC_APP_NAME) -> NBAuthentication:
    """To be used out of the webserver context"""
    app = Sanic(name)
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
