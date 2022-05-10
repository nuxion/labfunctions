import os
from datetime import datetime, timedelta

import aioredis
import jwt
import pytest

from labfunctions import defaults
from labfunctions.conf.server_settings import settings
from labfunctions.security import scopes
from labfunctions.security.authentication import Auth
from labfunctions.security.password import PasswordScript
from labfunctions.security.redis_tokens import RedisTokenStore
from labfunctions.security.scopes import scope2dict
from labfunctions.security.scopes import validate as validate_scopes
from labfunctions.security.utils import open_keys
from labfunctions.types.config import SecuritySettings
from labfunctions.types.security import JWTConfig, KeyPairs


def test_security_password_script():
    ps = PasswordScript(salt="testing-salt")
    encrypted = ps.encrypt("password-test")

    valid = ps.verify("password-test", encrypted)
    invalid = ps.verify("password-invalid", encrypted)

    assert isinstance(encrypted, bytes)
    assert valid
    assert invalid is False


def test_security_open_keys():
    keys = open_keys("tests/ecdsa.pub.pem", "tests/ecdsa.priv.pem")
    assert isinstance(keys, KeyPairs)
    assert "GSM49Ag" in keys.public


def test_security_Auth_encode():
    keys = open_keys("tests/ecdsa.pub.pem", "tests/ecdsa.priv.pem")
    conf = JWTConfig(alg="ES512", keys=keys)
    a = Auth(conf)
    encoded = a.encode({"test": "hi"})
    original = a.decode(encoded)

    _exp = datetime.utcnow() - timedelta(minutes=1)
    encoded_invalid = a.encode({}, exp=_exp)
    with pytest.raises(jwt.ExpiredSignatureError):
        a.decode(encoded_invalid)

    assert isinstance(encoded, str)
    assert original["test"] == "hi"
    assert "exp" in original.keys()


# def test_security_Auth_from_settings():
#     s = Settings(BASE_PATH=os.getcwd())
#     auth = Auth.from_settings(s)
#     assert isinstance(auth, Auth)


def test_security_scope2dict():
    _scopes = ["user", "admin:read:write", ":read:write"]
    dict_ = scopes.scope2dict(_scopes)

    assert "user" in dict_.keys()
    assert "admin" in dict_.keys()
    assert len(dict_["admin"]) == 2
    assert "any" in dict_["user"]
    assert dict_["any"]


def test_security_validate_scopes():
    scopes1 = ["user"]
    required1 = ["something"]
    valid1 = validate_scopes(required1, scopes1)

    scopes2 = ["user"]
    required2 = ["user"]
    valid2 = validate_scopes(required2, scopes2)

    scopes3 = ["user:read"]
    required3 = ["user"]
    valid3 = validate_scopes(required3, scopes3)

    scopes4 = ["user:read"]
    required4 = ["user:write"]
    valid4 = validate_scopes(required4, scopes4)

    scopes5 = ["user:read"]
    required5 = ["user:read:write"]
    valid5 = validate_scopes(required5, scopes5)

    scopes6 = ["user:read"]
    required6 = ["user:read:write", "admin:write"]
    valid6 = validate_scopes(required6, scopes6)

    scopes7 = ["user:read"]
    required7 = ["user:read:write", "admin:write"]
    valid7 = validate_scopes(required7, scopes7, require_all=False)

    scopes8 = ["user:write"]
    required8 = [":read"]
    valid8 = validate_scopes(required8, scopes8)

    scopes9 = [":read"]
    required9 = [":read"]
    valid9 = validate_scopes(required9, scopes9)

    scopes10 = [":read"]
    required10 = ["test:read", "admin:read"]
    valid10 = validate_scopes(required10, scopes10)

    # it should be valid. It required that namespace match
    scopes11 = ["user:read"]
    required11 = [":read"]
    valid11 = validate_scopes(required11, scopes11)

    assert not valid1
    assert valid2
    assert valid3
    assert not valid4
    assert valid5
    assert not valid6
    assert valid7
    assert not valid8
    assert valid9
    assert not valid10
    assert not valid11  # review


def test_security_redis_store():
    redis = aioredis.from_url(settings.WEB_REDIS)
    store = RedisTokenStore(redis, "test")

    store2 = RedisTokenStore(settings.WEB_REDIS, "test")
    assert isinstance(store.redis, aioredis.Redis)
    assert isinstance(store2.redis, aioredis.Redis)
    assert store2.ns == "test"


@pytest.mark.asyncio
async def test_security_redis_put(mocker):
    mock = mocker.AsyncMock()
    mock.set.return_value = "ok"

    mocker.patch(
        "labfunctions.security.redis_tokens.aioredis.from_url", return_value=mock
    )
    store = RedisTokenStore("test", "test")
    rsp = await store.put("test", "hey", ttl=5)
    assert rsp
    assert mock.mock_calls[0][1][0] == "test:test"


@pytest.mark.asyncio
async def test_security_redis_get(mocker):

    redis = aioredis.from_url(settings.WEB_REDIS, decode_responses=True)
    store = RedisTokenStore(redis.client(), "test")
    await store.put("test_key", "ok")
    rsp = await store.get("test_key")
    assert rsp == "ok"


def test_security_redis_generate(mocker):
    mock = mocker.AsyncMock()
    mocker.patch(
        "labfunctions.security.redis_tokens.aioredis.from_url", return_value=mock
    )
    # store = RedisTokenStore("test", "test")
    tkn = RedisTokenStore.generate()
    assert tkn
