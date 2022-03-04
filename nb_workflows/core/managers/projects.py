from datetime import datetime
from typing import List, Optional, Tuple, Union

from sqlalchemy import delete, exc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from nb_workflows.conf import settings
from nb_workflows.core.entities import ProjectData, ProjectReq
from nb_workflows.core.models import ProjectModel
from nb_workflows.hashes import generate_random
from nb_workflows.utils import get_parent_folder, secure_filename


def select_project():
    stmt = select(ProjectModel).options(selectinload(ProjectModel.user))
    return stmt


def _model2projectdata(obj: ProjectModel) -> ProjectData:
    pd = ProjectData(
        name=obj.name,
        projectid=obj.projectid,
        username=obj.user.username,
        description=obj.description,
        respository=obj.repository,
    )
    return pd


def _create_or_update_stmt(name, user_id: int, projectid: str, pd: ProjectData):
    stmt = insert(ProjectModel.__table__).values(
        name=name,
        projectid=projectid,
        description=pd.description,
        repository=pd.repository,
        user_id=user_id,
    )
    stmt = stmt.on_conflict_do_update(
        # constraint="crawlers_page_bucket_id_fkey",
        index_elements=[projectid],
        set_=dict(
            description=pd.description,
            repository=pd.repository,
            updated_at=datetime.utcnow(),
        ),
    )

    return stmt


def normalize_name(name: str) -> str:
    evaluate = name.lower()
    evaluate = evaluate.replace(" ", "_")
    evaluate = secure_filename(name)
    return evaluate


def generate_projectid() -> str:
    return generate_random(settings.PROJECTID_LEN)


async def create(
    session, user_id: int, pq: ProjectReq
) -> Union[ProjectModel, None]:
    name = normalize_name(pq.name)

    projectid = pq.projectid or generate_projectid()
    pm = ProjectModel(
        name=name,
        projectid=projectid,
        description=pq.description,
        repository=pq.repository,
        user_id=user_id,
    )
    session.add(pm)
    try:
        await session.commit()
    except exc.IntegrityError:
        await session.rollback()
        return None
    return pm


async def create_or_update(session, user_id: int, pq: ProjectReq):
    name = normalize_name(pq.name)
    projectid = generate_projectid()
    stmt = _create_or_update_stmt(name, user_id, projectid, pq)
    await session.execute(stmt)
    obj = await get_by_name_model(session, name)
    return obj


async def get_by_projectid_model(session, projectid) -> Union[ProjectModel, None]:
    stmt = select_project().where(ProjectModel.projectid == projectid).limit(1)
    r = await session.execute(stmt)
    obj: Optional[ProjectModel] = r.scalar_one_or_none()
    if not obj:
        return None
    return obj


async def get_by_projectid(
    session, projectid, user_id=None
) -> Union[ProjectData, None]:

    stmt = select_project().where(ProjectModel.projectid == projectid)
    if user_id:
        stmt = stmt.where(ProjectModel.user_id == user_id)
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
        return ProjectData(
            **obj.to_dict(rules=("-id", "-created_at", "-updated_at"))
        )
    return None


async def list_all(session, user_id=None) -> Union[List[ProjectData], None]:
    stmt = select_project()
    if user_id:
        stmt = stmt.where(ProjectModel.user_id == user_id)
    rows = await session.execute(stmt)

    if rows:
        results = [_model2projectdata(r[0]) for r in rows]
        return results
    return None


async def list_by_user(session, user_id) -> Union[List[ProjectData], None]:
    stmt = select_project().where(ProjectModel.user_id == user_id)
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


def ask_project_name() -> str:
    parent = get_parent_folder()
    _default = normalize_name(parent)
    project_name = str(
        input(f"Write a name for this project (default: {_default}): ")
        or _default
    )
    name = normalize_name(project_name)
    return name
