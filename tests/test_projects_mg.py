import logging

import pytest

from nb_workflows import defaults
from nb_workflows import defaults as df
from nb_workflows.managers import projects_mg
from nb_workflows.models import ProjectModel, UserModel
from nb_workflows.types import ProjectData

from .factories import (
    ProjectDataFactory,
    ProjectReqFactory,
    create_project_model,
    create_user_model2,
)


def test_projects_mg_model2pd():

    um = create_user_model2()
    pm = create_project_model(um)

    pd = projects_mg._model2projectdata(pm)
    assert isinstance(pd, ProjectData)


@pytest.mark.asyncio
async def test_projects_mg_create_or_update(async_session):
    um = create_user_model2()
    um.id = 99
    async_session.add(um)
    await async_session.flush()
    pq = ProjectReqFactory()
    pm = await projects_mg.create_or_update(async_session, um.id, pq)
    pq.description = "changed"
    pm2 = await projects_mg.create_or_update(async_session, um.id, pq)
    assert isinstance(pm, ProjectModel)
    assert pm2.description == pq.description


@pytest.mark.asyncio
async def test_projects_mg_create(async_session):
    um = create_user_model2()
    um.id = 100
    async_session.add(um)
    await async_session.flush()
    pq = ProjectReqFactory()
    pd = await projects_mg.create(async_session, um.id, pq)
    pd2 = await projects_mg.create(async_session, um.id, pq)
    assert isinstance(pd, ProjectData)
    assert pd2 is None
    assert pd.agent == f"{defaults.AGENT_USER_PREFIX}{pd.projectid}"


@pytest.mark.asyncio
async def test_projects_mg_assign_project(async_session):
    um = create_user_model2()
    async_session.add(um)
    await async_session.flush()
    # pq = ProjectReqFactory()
    res_true = await projects_mg.assign_project(async_session, um.username, "test")
    pd = await projects_mg.get_by_projectid(async_session, "test")

    res_false = await projects_mg.assign_project(async_session, "not exist", "test")
    assert um.username in pd.users
    assert res_true
    assert res_false is False


@pytest.mark.asyncio
async def test_projects_mg_delete(async_session):
    um = create_user_model2()
    pm = create_project_model(um)
    await projects_mg.delete_by_projectid(async_session, pm.projectid)
    pm_deleted = await projects_mg.get_by_projectid(async_session, pm.projectid)
    assert pm_deleted is None


@pytest.mark.asyncio
async def test_projects_mg_agent_get(async_session):
    agent = await projects_mg.get_agent(async_session, "admin_test", "test")
    assert isinstance(agent, UserModel)


@pytest.mark.asyncio
async def test_projects_mg_agent_delete(async_session):
    res = await projects_mg.create_agent(async_session, "test")
    deleted = await projects_mg.delete_agent(async_session, res.username, "test")
    agent = await projects_mg.get_agent(async_session, res.username)

    isfalse = await projects_mg.delete_agent(async_session, "non_exist", "test")
    assert agent is None
    assert deleted
    assert isfalse is False


@pytest.mark.asyncio
async def test_projects_mg_agent_create(async_session):
    normal_agent = await projects_mg.create_agent(async_session, "test")
    admin = await projects_mg.create_agent(async_session, "test2", is_admin=True)
    normal = await projects_mg.get_agent(async_session, normal_agent.username, "test")

    assert normal_agent
    assert "test" in normal.projects[0].name
    assert normal.scopes == defaults.AGENT_SCOPES
    assert admin.scopes == defaults.AGENT_ADMIN_SCOPES


@pytest.mark.asyncio
async def test_projects_mg_get_privk(async_session):
    key = await projects_mg.get_private_key(async_session, "test")
    no_key = await projects_mg.get_private_key(async_session, "nokey")

    assert isinstance(key, str)
    assert no_key is None


def test_projects_mg_get_privk_sync(session):
    key = projects_mg.get_private_key_sync(session, "test")
    no_key = projects_mg.get_private_key_sync(session, "nokey")

    assert isinstance(key, str)
    assert no_key is None
