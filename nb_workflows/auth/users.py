from datetime import datetime
from typing import Union

from sanic_jwt import exceptions
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from nb_workflows.auth.models import GroupModel, UserModel
from nb_workflows.utils import password_manager


def create_user(
    session, username, password, superuser=False, is_active=False
) -> UserModel:
    pm = password_manager()
    key = pm.encrypt(password)
    u = UserModel(
        username=username,
        password=key,
        is_superuser=superuser,
        is_active=is_active,
    )
    session.add(u)
    return u


def get_user(session, username: str) -> Union[UserModel, None]:
    stmt = select(UserModel).where(UserModel.username == username).limit(1)
    user_t = session.execute(stmt).fetchone()
    if user_t:
        return user_t[0]
    return None


async def get_user_async(session, username: str) -> Union[UserModel, None]:
    stmt = (
        select(UserModel)
        .where(UserModel.username == username)
        .options(selectinload(UserModel.groups))
        .limit(1)
    )
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

        return user.to_dict()
