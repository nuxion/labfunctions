from datetime import datetime
from functools import wraps
from inspect import isawaitable
from typing import Optional, Union

from pydantic.error_wrappers import ValidationError
from sanic import Request
from sqlalchemy import delete
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from labfunctions import defaults
from labfunctions.hashes import generate_random
from labfunctions.models import ProjectModel, UserModel, assoc_projects_users
from labfunctions.security import AuthSpec, PasswordScript, get_delta
from labfunctions.security.errors import (
    AuthValidationFailed,
    MissingAuthorizationHeader,
    WebAuthFailed,
)
from labfunctions.types.security import JWTResponse, UserLogin
from labfunctions.types.user import UserOrm


def select_user():
    stmt = select(UserModel).options(
        selectinload(UserModel.projects),
    )
    # stmt = select(UserModel)
    return stmt


def join_with_project(username):
    stmt = select_user().join(ProjectModel.users).where(UserModel.username == username)
    return stmt


def join_by_project():
    stmt = select_user().join(ProjectModel.users)
    return stmt


def model2orm(user: UserModel) -> UserOrm:
    projects = []
    if user.projects:
        projects = [p.name for p in user.projects]

    return UserOrm(
        username=user.username,
        id=user.id,
        email=user.email,
        password=user.password,
        scopes=user.scopes,
        is_superuser=user.is_superuser,
        is_agent=user.is_agent,
        projects=projects,
    )


def _insert(user: UserOrm):
    t = UserModel.__table__
    stmt = (
        sqlinsert(t).values(**user.dict(exclude={"projects", "id"})).returning(t.c.id)
    )
    return stmt


def _insert_project_user(project_id, user_id):
    stmt = sqlinsert(assoc_projects_users).values(project_id, user_id)


def encrypt_password(password, salt: Union[bytes, str]):

    pm = PasswordScript(salt)
    encrypted = pm.encrypt(password)
    return encrypted


def create(
    session,
    u: UserOrm,
    password: Optional[str] = None,
    salt: Optional[str] = None,
) -> Union[UserModel, None]:
    """
    it will create a user in  database
    if created will return the id, else None
    """
    if u.is_superuser and "admin:read:write" not in u.scopes:
        u.scopes = f"{u.scopes},admin:r:w"

    if password and salt:
        u.password = encrypt_password(password, salt)

    um = UserModel(**u.dict(exclude={"projects"}))
    session.add(um)
    try:
        session.flush()
        return um
    except IntegrityError:
        pass
    # try:
    # um = UserModel(**u.dict())
    #    r = session.execute(stmt)
    #    id = r.scalar()
    #    return id
    # except IntegrityError:
    #    session.rollback()

    return None


async def get_user_async(
    session, username: str, projectid: Optional[str] = None
) -> Union[UserModel, None]:
    stmt = select_user().where(UserModel.username == username).limit(1)
    if projectid:
        stmt = join_with_project(username).limit(1)

    rsp = await session.execute(stmt)
    return rsp.scalar_one_or_none()


async def get_userid_async(session, user_id: str) -> Union[UserModel, None]:
    stmt = select_user().where(UserModel.id == user_id).limit(1)

    rsp = await session.execute(stmt)
    return rsp.scalar_one_or_none()


def get_user(session, username: str) -> Union[UserModel, None]:
    stmt = select(UserModel).where(UserModel.username == username).limit(1)
    rsp = session.execute(stmt)

    return rsp.scalar_one_or_none()


def create_or_update(session, user: UserOrm) -> UserModel:
    m = UserModel(**user.dict())

    session.merge(m)
    return m


def disable_user(session, username: str) -> Union[UserModel, None]:
    user = get_user(session, username)
    if user:
        user.is_active = False
        user.updated_at = datetime.utcnow()
        session.add(user)

        return user
    return None


async def delete_user_async(session, username: str):
    stmt = delete(UserModel).where(UserModel.username == username)
    await session.execute(stmt)


def delete_user(session, username: str):
    stmt = delete(UserModel).where(UserModel.username == username)
    session.execute(stmt)


async def disable_user_async(session, username: str) -> Union[UserModel, None]:
    user = await get_user_async(session, username)
    if user:
        user.is_active = False
        user.updated_at = datetime.utcnow()
        session.add(user)

        return user
    return None


async def change_pass_async(session, username: str, new_password: str, salt):
    u = await get_user_async(session, username)
    if u:
        pass_ = encrypt_password(new_password, salt=salt)
        u.password == pass_
        u.updated_at = datetime.utcnow()
        session.add(u)


def change_pass(session, user: str, new_password: str, salt) -> bool:
    obj = get_user(session, user)
    if obj:
        pass_ = encrypt_password(new_password, salt=salt)
        obj.password = pass_
        obj.updated_at = datetime.utcnow()
        session.add(obj)
        return True
    return False


def verify_password(
    user: UserModel, pass_unencrypted: str, salt: Union[bytes, str]
) -> bool:
    pm = PasswordScript(salt)
    verified = pm.verify(pass_unencrypted, user.password)
    if verified and user.is_active:
        return True
    return False


async def authenticate(request: Request, *args, **kwargs):
    try:
        creds = UserLogin(**request.json)
    except ValidationError as e:
        raise AuthValidationFailed()

    session = request.ctx.session
    async with session.begin():
        user = await get_user_async(session, creds.username)
        if user is None:
            raise AuthValidationFailed()

        is_valid = verify_password(
            user, creds.password, salt=request.app.config.AUTH_SALT
        )
        if not is_valid:
            raise AuthValidationFailed()

        return user


async def get_jwt_token(auth: AuthSpec, user: UserModel, exp=30) -> JWTResponse:
    access_token = auth.encode(
        {"usr": user.username, "scopes": user.scopes.split(",")},
        exp=get_delta(exp),
    )
    username = str(user.username)
    rftkn = await auth.store_refresh_token(username)
    return JWTResponse(access_token=access_token, refresh_token=rftkn)


def inject_user(func):
    """Inject a user"""

    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            token = request.ctx.token_data
            session = request.ctx.session
            user = get_user_async(session, token["usr"])
            if isawaitable(user):
                user = await user
            if not user:
                raise WebAuthFailed("Authentication failed")
            user_orm = model2orm(user)
            response = f(request, user=user_orm, *args, **kwargs)
            if isawaitable(response):
                response = await response

            return response

        return decorated_function

    return decorator(func)
