from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

from sqlalchemy import delete, exc
from sqlalchemy import insert as sqlinsert
from sqlalchemy import select

# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from nb_workflows import secrets
from nb_workflows.conf.server_settings import settings
from nb_workflows.hashes import generate_random
from nb_workflows.managers import users_mg
from nb_workflows.models import ProjectModel, UserModel, assoc_projects_users
from nb_workflows.types import ProjectData, ProjectReq
from nb_workflows.utils import get_parent_folder, secure_filename


def select_project():
    stmt = (
        select(ProjectModel)
        .options(selectinload(ProjectModel.owner))
        .options(selectinload(ProjectModel.agent))
        .options(selectinload(ProjectModel.users))
    )

    return stmt


def _model2projectdata(obj: ProjectModel) -> ProjectData:
    agent_name = None
    if obj.agent:
        agent_name = obj.agent.username

    pd = ProjectData(
        name=obj.name,
        projectid=obj.projectid,
        owner=obj.owner.username,
        users=[u.username for u in obj.users],
        agent=agent_name,
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


# def _create_or_update_stmt(name, user_id: int, projectid: str, pq: ProjectReq):
#     # _key = secrets.generate_private_key()
#
#     stmt = insert(ProjectModel.__table__).values(
#         name=name,
#         private_key=pq.private_key.encode("utf-8"),
#         projectid=projectid,
#         description=pq.description,
#         repository=pq.repository,
#         owner_id=user_id,
#     )
#     stmt = stmt.on_conflict_do_update(
#         # constraint="crawlers_page_bucket_id_fkey",
#         index_elements=[projectid],
#         set_=dict(
#             description=pq.description,
#             repository=pq.repository,
#             updated_at=datetime.utcnow(),
#         ),
#     )
#
#     return stmt


def normalize_name(name: str) -> str:
    evaluate = name.lower()
    evaluate = evaluate.replace(" ", "_")
    evaluate = secure_filename(name)
    return evaluate


def generate_projectid() -> str:
    return generate_random(settings.PROJECTID_LEN)


async def create(session, user_id: int, pq: ProjectReq) -> Union[ProjectData, None]:

    projectid = pq.projectid or generate_projectid()
    stmt = _insert(user_id, pq, projectid)
    project = _insert_relation_project(user_id, projectid)
    # session.add(pm)
    try:
        await session.execute(stmt)
        await session.execute(project)
        await session.commit()
    except exc.IntegrityError as e:
        # await session.rollback()
        return None

    return ProjectData(
        name=pq.name,
        projectid=projectid,
        description=pq.description,
        repository=pq.repository,
    )


async def assign_project(session, user_id: int, projectid):
    """
    Assign a user to a project.
    """
    um = await users_mg.get_userid_async(session, user_id)
    if um:
        # projects = [p.projectid for p in um.projects]
        # if projectid in projects:
        stmt = _insert_relation_project(user_id, projectid)
        await session.execute(stmt)
        return True
    return False


async def create_agent_for_project(session, projectid: str) -> Union[str, None]:
    prj = await get_by_projectid_model(session, projectid)
    if prj and not prj.agent_id:
        um = await users_mg.create_agent(session)
        um.projects.append(prj)
        prj.agent = um
        prj.updated_at = datetime.utcnow()
        session.add(prj)
        return um.username
    return None


async def get_agent_for_project(session, projectid: str) -> Union[UserModel, None]:
    prj = await get_by_projectid_model(session, projectid)
    if prj and prj.agent_id:
        user = await users_mg.get_userid_async(session, prj.agent_id)
        return user
    return None


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


def get_by_projectid_model_sync(session, projectid) -> Union[ProjectModel, None]:
    stmt = select_project().where(ProjectModel.projectid == projectid).limit(1)
    r = session.execute(stmt)
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


async def get_by_name_model(session, name) -> Union[ProjectModel, None]:
    _name = normalize_name(name)
    stmt = select_project()
    stmt = stmt.where(ProjectModel.name == _name).limit(1)
    r = await session.execute(stmt)
    obj: Optional[ProjectModel] = r.scalar_one_or_none()
    if not obj:
        return None
    return obj


async def get_by_name(session, name) -> Union[ProjectData, None]:
    obj = await get_by_name_model(session, name)
    if obj:
        return ProjectData(**obj.to_dict(rules=("-id", "-created_at", "-updated_at")))
    return None


async def list_all(session, user_id=None) -> Union[List[ProjectData], None]:
    stmt = select_project()
    if user_id:
        stmt = stmt.where(ProjectModel.owner_id == user_id)
    rows = await session.execute(stmt)

    if rows:
        results = [_model2projectdata(r[0]) for r in rows]
        return results
    return None


async def list_by_user(session, user_id) -> Union[List[ProjectData], None]:
    stmt = select_project().where(ProjectModel.owner_id == user_id)
    rows = await session.execute(stmt)
    if rows:
        results = [_model2projectdata(r[0]) for r in rows]
        return results
    return None


async def delete_by_projectid(session, projectid):
    """TODO: In the future this could be a task
    or a flag that a async task takes to clean project data
    such as docker images, files and so on.
    """
    stmt = delete(ProjectModel).where(ProjectModel.projectid == projectid)
    await session.execute(stmt)


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
