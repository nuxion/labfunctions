from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set

import jwt
from pydantic.error_wrappers import ValidationError

from labfunctions import defaults
from labfunctions.security import scopes
from labfunctions.types.config import SecuritySettings
from labfunctions.types.security import JWTConfig, JWTResponse
from labfunctions.utils import get_class

from .base import AuthSpec, TokenStoreSpec
from .errors import AuthValidationFailed
from .utils import get_delta, open_keys


class Auth(AuthSpec):
    def __init__(self, conf: JWTConfig, store: Optional[TokenStoreSpec] = None):
        """
        It is a wrapper around jwt which produces jwt tokens.
        By default it will add a "exp" claim, other claims.

        Standard claims could be configurated from JWTConfing or when passing
        a payload to encode. In that case if both configurations exists, it will
        prioritize the payload configuration.
        """
        self.conf = conf
        self.store = store

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
            exp = get_delta(self.conf.exp_min)
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

    async def store_refresh_token(self, username: str, ttl=None) -> str:
        ttl = ttl or self.conf.ttl_refresh_token
        refresh = self.store.generate()
        await self.store.put(f"{username}.{refresh}", username, ttl=ttl)

        return refresh

    async def validate_refresh_token(self, access_token, refresh_token) -> bool:
        is_valid = False
        decoded = self.decode(access_token, verify_exp=False)
        value = await self.store.get(f"{decoded['usr']}.{refresh_token}")
        if decoded["usr"] == value:
            is_valid = True
        return is_valid

    async def refresh_token(self, access_token, refresh_token) -> JWTResponse:
        is_valid = await self.validate_refresh_token(access_token, refresh_token)
        if is_valid:
            decoded = self.decode(access_token, verify_exp=False)
            await self.store.delete(f"{decoded['usr']}.{refresh_token}")

            _new_refresh = await self.store_refresh_token(decoded["usr"])
            _new_tkn = self.encode(decoded)
            new_jwt = JWTResponse(access_token=_new_tkn, refresh_token=_new_refresh)
            return new_jwt
        raise AuthValidationFailed()


def auth_from_settings(
    settings: SecuritySettings, store: Optional[TokenStoreSpec] = None
) -> AuthSpec:
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
    return AuthClass(conf, store=store)
