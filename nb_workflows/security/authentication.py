from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

import jwt
from pydantic.error_wrappers import ValidationError
from sanic import Request

from nb_workflows import defaults
from nb_workflows.errors.security import AuthValidationFailed
from nb_workflows.security import scopes
from nb_workflows.security.utils import generate_token
from nb_workflows.types.config import SecuritySettings
from nb_workflows.types.security import JWTConfig, JWTResponse
from nb_workflows.utils import get_class

from .base import AuthSpec
from .utils import open_keys


def _get_delta(delta_min: int) -> int:
    """Returns a timestamp addding a delta_min value to the utc now date."""
    delta = datetime.utcnow() + timedelta(minutes=delta_min)
    return int(delta.timestamp())


async def store_refresh_token(redis, username: str) -> str:
    tkn = generate_token()
    await redis.set(f"rtkn:{tkn}", username)
    return tkn


async def validate_refresh_token(redis, token, user):

    redis_user = await redis.get(f"rtkn:{token}")
    if redis_user and redis_user == user:
        return True
    return False


async def renew_refresh_token(redis, old_token, username: str) -> str:
    tkn = generate_token()
    async with redis.pipeline() as pipe:
        await pipe.delete(f"rtkn:{old_token}").set(f"rtkn:{tkn}", username).execute()
    return tkn


class Auth(AuthSpec):
    def __init__(self, conf: JWTConfig):
        """
        It is a wrapper around jwt which produces jwt tokens.
        By default it will add a "exp" claim, other claims.

        Standard claims could be configurated from JWTConfing or when passing
        a payload to encode. In that case if both configurations exists, it will
        prioritize the payload configuration.
        """
        self.conf = conf

    def _get_secret_encode(self):
        """because jwt allows the use of a simple secret or a pairs of keys
        this function will look at the configuration to determine a secret to be used
        """
        if self.conf.keys:
            _secret = self.conf.keys.private
        else:
            _secret = self.conf.secret
        return _secret

    def _get_secret_decode(self):
        if self.conf.keys:
            _secret = self.conf.keys.public
        else:
            _secret = self.conf.secret
        return _secret

    def _build_payload(self, payload: Dict[str, Any], exp=None, iss=None, aud=None):
        _payload = deepcopy(payload)
        if not exp:
            exp = _get_delta(self.conf.exp_min)
        _iss = iss or self.conf.issuer
        if _iss:
            _payload.update({"iss": _iss})

        _aud = aud or self.conf.audience
        if _aud:
            _payload.update({"aud": _aud})

        _payload.update({"exp": exp})
        return _payload

    def encode(self, payload: Dict[str, Any], exp=None, iss=None, aud=None) -> str:
        """Encode a payload into a JWT Token.

        Some standards claims like exp, iss and aud could be
        overwritten using this params.

        :param payload: a dictionary with any k/v pairs to add
        :param exp:  the “exp” (expiration time) claim identifies the expiration
        time on or after which the JWT MUST NOT be accepted for processing.
        if date or int is given it will overwrite the default configuration.
        :param iss: the “iss” (issuer) claim identifies the principal that issued the JWT.
        :param aud: The “aud” (audience) claim identifies the recipients that the JWT
        is intended for.
        """
        _secret = self._get_secret_encode()

        final = self._build_payload(payload, exp, iss, aud)

        encoded = jwt.encode(
            final,
            _secret,
            algorithm=self.conf.alg,
        )
        return encoded

    def decode(
        self, encoded, verify_signature=True, verify_exp=True, iss=None, aud=None
    ) -> Dict[str, Any]:
        _secret = self._get_secret_decode()

        _iss = iss or self.conf.issuer
        _aud = aud or self.conf.audience

        return jwt.decode(
            encoded,
            _secret,
            options={
                "verify_signature": verify_signature,
                "verify_exp": verify_exp,
                "require": self.conf.requires_claims,
            },
            aud=_aud,
            iss=_iss,
            algorithms=[self.conf.alg],
        )

    def validate(
        self,
        token: str,
        required_scopes: Optional[List[str]],
        require_all=True,
        iss=None,
        aud=None,
    ) -> Dict[str, Any]:
        try:
            decoded = self.decode(token, iss=iss, aud=aud)
            if required_scopes:
                user_scopes: List[str] = decoded["scopes"]
                valid = scopes.validate(
                    required_scopes, user_scopes, require_all=require_all
                )
                if not valid:
                    raise AuthValidationFailed()
        except jwt.InvalidTokenError as e:
            raise AuthValidationFailed()

        return decoded

    async def refresh_token(self, redis, access_token, refresh_token) -> JWTResponse:
        decoded = self.decode(access_token, verify_exp=False)
        is_valid = await validate_refresh_token(redis, refresh_token, decoded["usr"])
        if is_valid:
            _new_refresh = await renew_refresh_token(
                redis, refresh_token, decoded["usr"]
            )
            _new_tkn = self.encode(decoded)
            new_jwt = JWTResponse(access_token=_new_tkn, refresh_token=_new_refresh)
            return new_jwt
        raise AuthValidationFailed()

    async def store_refresh_token(self, redis, username: str) -> str:
        return await store_refresh_token(redis, username)


def auth_from_settings(settings: SecuritySettings) -> AuthSpec:
    """Intiliazie a `Auth` based on settings."""
    AuthClass = get_class(settings.AUTH_CLASS)
    keys = open_keys(settings.JWT_PUBLIC, settings.JWT_PRIVATE)
    conf = JWTConfig(
        alg=settings.JWT_ALG,
        exp_min=settings.JWT_EXP,
        keys=keys,
        issuer=settings.JWT_ISS,
        audience=settings.JWT_AUD,
        requires_claims=settings.JWT_REQUIRES_CLAIMS,
    )
    return AuthClass(conf)
