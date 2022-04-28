from dataclasses import asdict

import pytest
from pytest_mock import MockerFixture
from sanic import Sanic, response

from .factories import ProjectDataFactory, ProjectReqFactory


@pytest.mark.asyncio
async def test_projects_bp_generate(async_session, sanic_app):
    user_pass = {"username": "admin_test", "password": "meolvide"}
    req, res = await sanic_app.asgi_client.get("/v1/projects/_generateid")
    assert isinstance(res.json["projectid"], str)


@pytest.mark.asyncio
async def test_project_bp_create(
    async_session, sanic_app, access_token, mocker: MockerFixture
):
    prf = ProjectReqFactory(name="testing")
    pdf = ProjectDataFactory()
    # project_mock = mocker.patch(
    #     "nb_workflows.web.projects_bp.projects_mg.create", return_value=pdf)

    project_mock = mocker.patch(
        "nb_workflows.managers.projects_mg.create", return_value=pdf
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    req, res = await sanic_app.asgi_client.post(
        "/v1/projects", headers=headers, json=asdict(prf)
    )

    assert res.status_code == 201
    assert project_mock.call_args_list[0][0][2].projectid == prf.projectid
