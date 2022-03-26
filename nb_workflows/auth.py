import warnings
from datetime import datetime, timedelta

import jwt
from sanic import Sanic
from sanic.response import json
from sanic_jwt import Authentication, Claim, Configuration, Initialize, exceptions
from sanic_jwt import initialize as sanic_initialize
from sanic_jwt import utils

from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.managers.users_mg import (
    get_user_async,
    get_userid_async,
    verify_user_from_model,
)
from nb_workflows.types.users import UserData
from nb_workflows.utils import run_sync


class NBAuthWeb(Authentication):
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

            user_ = UserData.from_model(user)
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
            ud = UserData.from_model(user)
            return ud
        else:
            return None

    async def generate_refresh_token(self, request, user: UserData):
        """
        Generate a refresh token for a given user.
        TODO: this is temporally
        """
        warnings.warn("Refresh token never expires")

        redis = request.ctx.web_redis
        refresh_token = await redis.get(f"nb.rtkn.{user.user_id}")
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


class NBAuthStandalone:
    scopes_name = "scopes"

    def __init__(
        self,
        secret,
        alg="HS256",
        refresh_token_enabled=True,
        extend_payload=None,
        custom_claims=None,
        add_scopes_to_payload=None,
        expiration_delta_secs=1800,
    ):
        self._alg = alg
        self._secret = secret
        self._refresh_token_enabled = refresh_token_enabled = True
        self._payload = extend_payload
        self._custom_claims = custom_claims
        self._expiration_delta = expiration_delta_secs
        self._scopes = add_scopes_to_payload

    def build_claim_exp(self):
        delta = timedelta(seconds=self._expiration_delta)
        exp = datetime.utcnow() + delta
        return exp

    def generate_access_token(
        self, user: UserData, extend_payload=None, custom_claims=None, exp=None
    ):
        payload = self.build_payload(user, custom_claims, exp)
        if extend_payload:
            payload.update(extend_payload)

        access_token = jwt.encode(payload, self._secret, self._alg)
        return access_token

    def build_payload(self, user: UserData, custom_claims=None, exp=None):
        """
        Injects standard claims into the payload for: exp, iss, iat, nbf, aud.
        And, custom claims, if they exist
        """
        payload = {}

        _exp = exp or self.build_claim_exp()
        additional = {"exp": _exp}

        _claims = custom_claims or self._custom_claims

        payload.update(additional)

        if _claims:
            custom_claims = {}
            for claim in _claims:
                claim_data = claim.setup(payload, user)
                custom_claims[claim.get_key()] = claim_data
            payload.update(custom_claims)

        if self._scopes:
            payload.update({self.scopes_name: self._scopes(user)})

        return payload

    def decode(self, token, verify=True, verify_exp=True):
        decoded = jwt.decode(
            token,
            self._secret,
            algorithms=[self._alg],
            verify=verify,
            options={"verify_exp": verify_exp},
        )
        return decoded


class ProjectClaim(Claim):
    key = "projects"

    def setup(self, payload, user):
        return user.projects

    def verify(self, value):
        """
        admin role doesnt have a project assigned by default
        this could change in the future
        """
        # return value is not None
        return True


async def scope_extender(user, *args, **kwargs):
    return user.scopes


def scope_extender_sync(user, *args, **kwargs):
    return user.scopes


def initialize(name=defaults.SANIC_APP_NAME) -> NBAuthWeb:
    """To be used out of the webserver context"""
    app = Sanic(name)
    a = sanic_initialize(
        app,
        authentication_class=NBAuthWeb,
        secret=settings.SECRET_KEY,
        refresh_token_enabled=True,
    )
    return app.ctx.auth


# def get_auth_standalone(settings, custom_claims):


def get_auth() -> NBAuthWeb:
    """to get a NBAuthWeb instance from
    webserver cxt"""
    current = Sanic.get_app(defaults.SANIC_APP_NAME)
    return current.ctx.auth
