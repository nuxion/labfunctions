import pytest

from nb_workflows.executors import context
from nb_workflows.managers import users_mg
from nb_workflows.models import UserModel
from nb_workflows.types.security import JWTResponse
from nb_workflows.types.user import UserOrm

from .factories import UserOrmFactory, create_user_model2


# @pytest.mark.asyncio
def test_users_mg_create(session):
    u = UserOrmFactory()
    one = users_mg.create(session, u)
    u2 = UserOrmFactory(is_superuser=True)
    one = users_mg.create(session, u2)
    user_model = users_mg.get_user(session, u2.username)
    repeat = users_mg.create(session, u)
    # superuser = users_mg.create(session, u2)

    assert one
    assert repeat is None
    assert "admin:r:w" in user_model.scopes
    # assert superuser


@pytest.mark.asyncio
async def test_users_mg_get_async(async_session):
    um = await users_mg.get_user_async(async_session, "admin_test")
    non_exist = await users_mg.get_user_async(async_session, "non_exist")
    assert um
    assert non_exist is None


def test_users_mg_disable(session):
    u = users_mg.disable_user(session, "admin_test")
    non = users_mg.disable_user(session, "non_exist")

    assert u.is_active is False
    assert non is None


@pytest.mark.asyncio
async def test_users_mg_disable_async(async_session):
    u = await users_mg.disable_user_async(async_session, "admin_test")
    non = await users_mg.disable_user_async(async_session, "non_exist")

    assert u.is_active is False
    assert non is None


def test_users_mg_change_pass(session):
    u = "admin_test"
    rsp = users_mg.change_pass(session, "admin_test", "changetest", salt="test")
    um = users_mg.get_user(session, "admin_test")
    verified = users_mg.verify_password(um, "changetest", salt="test")

    assert rsp
    assert verified


def test_users_mg_verify_password(session):
    user = create_user_model2(password="test", salt="test")
    session.add(user)
    verified = users_mg.verify_password(user, pass_unencrypted="test", salt="test")
    assert verified


@pytest.mark.asyncio
async def test_users_mg_get_jwt(async_session, auth_helper, mocker):

    # async def refresh(us):
    #    return "refresh"

    # redis = mocker.MagicMock()
    # auth_helper.store_refresh_token = refresh
    user = create_user_model2(username="jwt_testing")

    jwt = await users_mg.get_jwt_token(auth_helper, user)
    assert isinstance(jwt, JWTResponse)
    assert jwt.refresh_token
