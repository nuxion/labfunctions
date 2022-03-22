from datetime import datetime
from typing import Union

from sanic_jwt import exceptions
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.hashes import PasswordScript, generate_random

# from nb_workflows.auth import gorups
from nb_workflows.models import UserModel
from nb_workflows.types.users import UserData


def select_user():
    stmt = select(UserModel).options(
        selectinload(UserModel.projects),
    )
    return stmt


def password_manager() -> PasswordScript:
    s = settings.SALT
    return PasswordScript(salt=s.encode("utf-8"))


def create_user(
    session, username, password, scopes, superuser=False, is_active=False
) -> UserModel:
    pm = password_manager()
    key = pm.encrypt(password)
    u = UserModel(
        username=username,
        password=key,
        scopes=scopes,
        is_superuser=superuser,
        is_active=is_active,
    )
    session.add(u)
    return u


async def create_agent(session, scopes=defaults.AGENT_SCOPES):
    name = generate_random(defaults.AGENT_LEN)
    fullname = f"{defaults.AGENT_USER_PREFIX}-{name}"

    u = UserModel(
        username=fullname,
        scopes=scopes,
    )

    session.add(u)
    return u


# async def assign_group(session, user: UserModel, group_name):
#     g_obj = await gorups.get_group_by_name(session, group_name)
#     user.groups.append(g_obj)
#
#
# def assign_group_sync(session, user: UserModel, group_name):
#     g_obj = gorups.get_group_by_name_sync(session, group_name)
#     if g_obj:
#         user.groups.append(g_obj)


def get_user(session, username: str) -> Union[UserModel, None]:
    stmt = select(UserModel).where(UserModel.username == username).limit(1)
    user_t = session.execute(stmt).fetchone()
    if user_t:
        return user_t[0]
    return None


async def get_user_async(session, username: str) -> Union[UserModel, None]:
    stmt = select_user().where(UserModel.username == username).limit(1)
    rsp = await session.execute(stmt)
    user_t = rsp.fetchone()
    if user_t:
        return user_t[0]
    return None


async def get_userid_async(session, id_: int) -> Union[UserModel, None]:
    stmt = select_user().where(UserModel.id == id_).limit(1)

    rsp = await session.execute(stmt)
    user_t = rsp.fetchone()
    if user_t:
        return user_t[0]
    return None


def disable_user(session, username) -> Union[UserModel, None]:
    user = get_user(session, username)
    if user:
        user.is_active = False
        user.updated_at = datetime.utcnow()
        session.add(user)

        return user
    return None


def change_scopes(session, username, new_scopes) -> Union[UserModel, None]:
    user = get_user(session, username)
    if user:
        user.scopes = new_scopes
        user.updated_at = datetime.utcnow()
        session.add(user)

        return user
    return None


def verify_user(session, username: str, password: str) -> Union[UserModel, None]:
    pm = password_manager()
    key = pm.encrypt(password)
    u = get_user(session, username)
    if u and u.is_active:
        is_valid = pm.verify(u.password, key)
        if is_valid:
            return u
    return None


def verify_user_from_model(user: UserModel, password: str) -> bool:
    pm = password_manager()
    # key = pm.encrypt(password)

    verified = pm.verify(password, user.password)
    if verified and user.is_active:
        return True
    return False


async def authenticate_web(requests, *args, **kwargs):
    u = requests.json.get("username", None)
    p = requests.json.get("password", None)
    session = requests.ctx.session
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


async def retrieve_user(request, payload, *args, **kwargs) -> UserData:
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


async def store_refresh_token(user_id, refresh_token, *args, **kwargs):

    redis = kwargs["request"].ctx.web_redis
    key = f"nb.rtkn.{user_id}"
    _key = await redis.get(key)
    if not _key:
        await redis.set(key, refresh_token)


async def retrieve_refresh_token(request, user_id, *args, **kwargs):
    # Check: https://github.com/ahopkins/sanic-jwt/issues/34
    redis = request.ctx.web_redis
    key = f"nb.rtkn.{user_id}"
    return await redis.get(key)
