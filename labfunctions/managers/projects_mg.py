from datetime import datetime
from inspect import isawaitable
from pathlib import Path
from typing import List, Optional, Tuple, Union

from sqlalchemy import delete, exc
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select

# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from labfunctions import defaults, secrets
from labfunctions.conf.server_settings import settings
from labfunctions.hashes import generate_random
from labfunctions.managers import users_mg
from labfunctions.models import ProjectModel, UserModel, assoc_projects_users
from labfunctions.types import ProjectData, ProjectReq
from labfunctions.utils import get_parent_folder, normalize_name


def select_project():
    stmt = (
        select(ProjectModel).options(selectinload(ProjectModel.owner))
        # .options(selectinload(ProjectModel.agent))
        .options(selectinload(ProjectModel.users))
    )

    return stmt


def _model2projectdata(obj: ProjectModel) -> ProjectData:
    # agent_name = None
    # if obj.agent:
    #     agent_name = obj.agent.username

    pd = ProjectData(
        name=obj.name,
        projectid=obj.projectid,
        owner=obj.owner.username,
        users=[u.username for u in obj.users],
        # agent=agent_name,
        description=obj.description,
        respository=obj.repository,
    )
    return pd


def _insert(user_id, pq: ProjectReq, projectid):

    table = ProjectModel.__table__
    name = normalize_name(pq.name)
    stmt = sqlinsert(table).values(
        name=name,
        private_key=pq.private_key.encode("utf-8"),
        projectid=projectid,
        description=pq.description,
        repository=pq.repository,
        owner_id=user_id,
    )
    return stmt


def _insert_relation_project(user_id, project_id):
    stmt = sqlinsert(assoc_projects_users).values(
        project_id=project_id, user_id=user_id
    )
    return stmt


def generate_projectid(name=None) -> str:
    return generate_random(
        settings.PROJECTID_LEN, alphabet=defaults.PROJECT_ID_ALPHABET
    )


async def create(session, user_id: int, pq: ProjectReq) -> Union[ProjectData, None]:

    projectid = pq.projectid or generate_projectid()
    stmt = _insert(user_id, pq, projectid)
    project = _insert_relation_project(user_id, projectid)
    # session.add(pm)
    try:
        await session.execute(stmt)
        await session.execute(project)
        agent_user = await create_agent(session, projectid)
        # await session.commit()
        await session.commit()
    except exc.IntegrityError as e:
        # await session.rollback()
        return None

    return ProjectData(
        name=pq.name,
        projectid=projectid,
        description=pq.description,
        repository=pq.repository,
        agent=agent_user.username,
    )


async def assign_project(session, username: str, projectid: str) -> bool:
    """
    Assign a user to a project.
    """
    um = await users_mg.get_user_async(session, username)
    if um:
        # projects = [p.projectid for p in um.projects]
        # if projectid in projects:
        stmt = _insert_relation_project(um.id, projectid)
        await session.execute(stmt)
        return True
    return False


async def create_or_update(session, user_id: int, pq: ProjectReq):
    name = normalize_name(pq.name)
    projectid = generate_projectid()
    pm = ProjectModel(
        name=name,
        private_key=pq.private_key.encode("utf-8"),
        projectid=projectid,
        description=pq.description,
        repository=pq.repository,
        owner_id=user_id,
    )

    # stmt = _create_or_update_stmt(name, user_id, projectid, pq)
    await session.merge(pm)
    # obj = await get_by_name_model(session, name)
    return pm


async def get_by_projectid_model(session, projectid) -> Union[ProjectModel, None]:
    stmt = select_project().where(ProjectModel.projectid == projectid).limit(1)
    r = await session.execute(stmt)
    return r.scalar_one_or_none()


async def get_by_projectid(
    session, projectid, user_id=None
) -> Union[ProjectData, None]:

    stmt = select_project().where(ProjectModel.projectid == projectid)
    if user_id:
        stmt = stmt.where(ProjectModel.owner_id == user_id)
    stmt = stmt.limit(1)
    r = await session.execute(stmt)
    obj: Optional[ProjectModel] = r.scalar_one_or_none()
    if not obj:
        return None
    return _model2projectdata(obj)


async def list_all(session, user_id=None) -> Union[List[ProjectData], None]:
    stmt = select_project()
    if user_id:
        stmt = stmt.where(ProjectModel.owner_id == user_id)
    rows = await session.execute(stmt)

    if rows:
        results = [_model2projectdata(r[0]) for r in rows]
        return results
    return None


# async def list_by_user(session, user_id) -> Union[List[ProjectData], None]:
#     stmt = select_project().where(ProjectModel.owner_id == user_id)
#     rows = await session.execute(stmt)
#     if rows:
#         results = [_model2projectdata(r[0]) for r in rows]
#         return results
#     return None


async def delete_by_projectid(session, projectid):
    """TODO: In the future this could be a task
    or a flag that a async task takes to clean project data
    such as docker images, files and so on.
    """
    stmt = delete(ProjectModel).where(ProjectModel.projectid == projectid)
    await session.execute(stmt)


async def create_agent(
    session,
    projectid=None,
    scopes=defaults.AGENT_SCOPES,
    admin_scopes=None,
    is_admin=False,
):
    prefix = generate_random(size=5)
    if projectid:
        prefix = projectid[:5]
    name = f"{prefix}-{generate_random(defaults.AGENT_LEN)}"
    fullname = f"{defaults.AGENT_USER_PREFIX}{name}"
    if is_admin:
        scopes = defaults.AGENT_ADMIN_SCOPES

    u = UserModel(
        username=fullname,
        scopes=scopes,
        is_agent=True,
    )
    if projectid:
        prj = await get_by_projectid_model(session, projectid)
        u.projects.append(prj)
        prj.updated_at = datetime.utcnow()
        session.add(prj)

    session.add(u)

    return u


async def get_agent(
    session, agentname: str, projectid: Optional[str] = None
) -> Union[UserModel, None]:
    # prj = await get_by_projectid_model(session, projectid)
    stmt = users_mg.join_with_project(agentname)

    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_agent_project(session, projectid) -> Union[UserModel, None]:
    stmt = (
        users_mg.join_by_project()
        .where(UserModel.is_agent.is_(True))
        .where(ProjectModel.projectid == projectid)
        .limit(1)
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_agent_list(session, projectid: Optional[str] = None) -> List[str]:
    stmt = users_mg.select_user().where(UserModel.is_agent.is_(True))
    if projectid:
        stmt = (
            users_mg.join_by_project()
            .where(UserModel.is_agent.is_(True))
            .where(ProjectModel.projectid == projectid)
        )

    res = session.execute(stmt)
    if isawaitable(res):
        res = await res
    return [r[0].username for r in res]


async def delete_agent(session, agentname, projectid: Optional[str] = None) -> bool:
    user = await users_mg.get_user_async(session, agentname, projectid)
    if user:
        await session.delete(user)
        return True
    return False
    # session.add(prj)


def get_private_key_sync(session, project_id) -> Union[str, None]:
    stmt = select(ProjectModel).where(ProjectModel.projectid == project_id).limit(1)
    r = session.execute(stmt)
    obj: Optional[ProjectModel] = r.scalar_one_or_none()
    if obj:
        return obj.private_key.decode("utf-8")
    return None


async def get_private_key(session, project_id) -> Union[str, None]:
    stmt = select(ProjectModel).where(ProjectModel.projectid == project_id).limit(1)
    r = await session.execute(stmt)
    obj: Optional[ProjectModel] = r.scalar_one_or_none()
    if obj:
        return obj.private_key.decode("utf-8")
    return None
