import logging

import pytest

from nb_workflows.conf import defaults as df
from nb_workflows.managers import projects_mg
from nb_workflows.types import ProjectData

from .factories import (
    ProjectDataFactory,
    ProjectReqFactory,
    create_project_model,
    create_user_model,
)

# def test_projects_mg_create_or_update():
#     wfid = "test"
#     pid = "pid-test"
#     wfd = WorkflowDataWebFactory()
#     stmt = workflows_mg._create_or_update_workflow(wfid, pid, wfd)
#     assert "wfid" in str(stmt)


@pytest.mark.asyncio
async def test_projects_mg_create(async_session):
    um = create_user_model()
    um.id = 100
    async_session.add(um)
    await async_session.flush()
    pq = ProjectReqFactory()
    pd = await projects_mg.create(async_session, um.id, pq)
    assert isinstance(pd, ProjectData)


@pytest.mark.asyncio
async def test_projects_mg_add_project(async_session):
    um = create_user_model()
    async_session.add(um)
    await async_session.flush()
    # pq = ProjectReqFactory()
    res = await projects_mg.assign_project(async_session, um.id, "test")
    pd = await projects_mg.get_by_projectid(async_session, "test")

    assert um.username in pd.users


@pytest.mark.asyncio
async def test_projects_mg_create_agent_for(async_session):
    res = await projects_mg.create_agent_for_project(async_session, "test")
    pd = await projects_mg.get_by_projectid(async_session, "test")

    agent = await projects_mg.get_agent_for_project(async_session, "test")

    assert res == pd.agent
    assert "test" in agent.projects[0].name
    assert agent.scopes == "agent:rw"
