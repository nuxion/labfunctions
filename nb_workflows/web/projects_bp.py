# pylint: disable=unused-argument
import json as std_json
import pathlib
from typing import List, Union

import httpx
from sanic import Blueprint, Request, Sanic, exceptions
from sanic.response import empty, json
from sanic_ext import openapi

from nb_workflows import defaults
from nb_workflows.client.types import Credentials
from nb_workflows.conf.server_settings import settings
from nb_workflows.defaults import API_VERSION
from nb_workflows.managers import projects_mg, users_mg
from nb_workflows.runtimes.context import build_upload_uri, create_build_ctx
from nb_workflows.scheduler import SchedulerExecutor
from nb_workflows.security import get_auth
from nb_workflows.security.web import protected
from nb_workflows.types import ExecutionResult, ProjectData, ProjectReq
from nb_workflows.types.projects import ProjectBuildReq
from nb_workflows.types.runtimes import RuntimeSpec
from nb_workflows.types.user import AgentReq, UserOrm
from nb_workflows.utils import run_async, secure_filename
from nb_workflows.web.utils import get_query_param2, stream_reader

projects_bp = Blueprint("projects", url_prefix="projects", version=API_VERSION)


async def generate_id(session, base_name, retries=3) -> Union[str, None]:
    ix = 0
    while ix <= retries:
        id_ = projects_mg.generate_projectid()
        r = await projects_mg.get_by_projectid(session, id_)
        if not r:
            return id_
        ix += 1

    return None


def _get_scheduler(qname=settings.RQ_CONTROL_QUEUE) -> SchedulerExecutor:

    current_app = Sanic.get_app(defaults.SANIC_APP_NAME)
    r = current_app.ctx.rq_redis
    return SchedulerExecutor(r, qname=qname)


def get_token_data(request: Request):
    return request.ctx.token_data


@projects_bp.get("/_generateid")
@openapi.response(200, "project")
@openapi.response(500, "not found")
async def project_generateid(request: Request):
    """Generates a random projectid"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    id_ = projects_mg.generate_projectid()
    async with session.begin():
        id_ = await generate_id(session, retries=3)
        if id_:
            return json(dict(projectid=id_), 200)
    return json(dict(msg="Error with generation of a id"), 500)


@projects_bp.post("/")
@openapi.body({"application/json": ProjectReq})
@openapi.response(201, ProjectData, "Created")
@protected()
@users_mg.inject_user
async def project_create(request, user: UserOrm):
    """Create a new project"""
    # pylint: disable=unused-argument

    dict_ = request.json
    token_data = get_token_data(request)
    pr = ProjectReq(**dict_)
    session = request.ctx.session
    r = await projects_mg.create(session, user.id, pr)
    if r:
        return json(r.dict(), 201)
    return json(dict(msg="already exist"), 200)


@projects_bp.put("/")
@openapi.body({"application/json": ProjectReq})
@openapi.response(202, "created")
@protected()
@users_mg.inject_user
async def project_create_or_update(request, user: UserOrm):
    """Create or update a project"""
    # pylint: disable=unused-argument

    dict_ = request.json
    pd = ProjectReq(**dict_)
    session = request.ctx.session
    async with session() as new_session:
        r = await projects_mg.create_or_update(new_session, user.id, pd)
    return json(dict(msg="created"), 202)


@projects_bp.get("/")
@openapi.response(200, List[ProjectData], "project-list")
@protected()
@users_mg.inject_user
async def project_list(request, user: UserOrm):
    """Get a list of projects belonging to a user"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    result = await projects_mg.list_all(session, user.id)
    return json([r.dict() for r in result], 200)


@projects_bp.get("/<projectid:str>")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, "project")
@openapi.response(404, "not found")
@protected()
@users_mg.inject_user
async def project_get_one(request, projectid, user: UserOrm):
    """Get one project"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    print("User id: ", user.id)
    r = await projects_mg.get_by_projectid(session, projectid, user_id=user.id)
    if r:
        return json(r.dict(), 200)
    return json(dict(msg="Not found"))


@projects_bp.delete("/<projectid:str>")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, "project")
@openapi.response(404, "not found")
@protected()
async def project_delete(request, projectid):
    """Delete Project"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    await projects_mg.delete_by_projectid(session, projectid)
    return json(dict(msg="deleted"))


@projects_bp.post("/<projectid:str>/agent")
@openapi.parameter("projectid", str, "path")
@protected()
async def project_create_user_agent(request, projectid):
    """
    Creates a User Agent
    """
    session = request.ctx.session
    async with session.begin():
        res = await projects_mg.create_agent_for_project(session, projectid)
        if res:
            return json(dict(msg=res), 201)

    return json(dict(msg="not created"), 200)


@projects_bp.delete("/<projectid:str>/agent")
@openapi.parameter("projectid", str, "path")
@protected()
async def project_delete_user_agent(request, projectid):
    """
    Delete a User Agent
    """
    session = request.ctx.session
    await projects_mg.delete_agent_for_project(session, projectid)
    return json(dict(msg="deleted"), 200)


@projects_bp.post("/<projectid:str>/agent/_token")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, Credentials, "agent credentials")
@protected()
async def project_get_agent_token(request, projectid):
    """
    Create an agent token
    """
    # pylint: disable=unused-argument
    _auth = get_auth(request)
    session = request.ctx.session
    redis = request.ctx.web_redis

    agt = await projects_mg.get_agent_for_project(session, projectid)
    jwt = await users_mg.get_jwt_token(_auth, agt, exp=settings.AGENT_TOKEN_EXP)

    return json(jwt.dict(), 200)


@projects_bp.post("/<projectid:str>/_build")
@openapi.body({"application/json": RuntimeSpec})
@openapi.parameter("version", str, "query")
@protected()
async def project_build(request, projectid):
    """
    Enqueue docker build image
    """
    # pylint: disable=unused-argument
    spec = RuntimeSpec(**request.json)

    root = pathlib.Path(projectid)

    version = get_query_param2(request, "version", None)

    session = request.ctx.session
    async with session.begin():
        pd = await projects_mg.get_by_projectid(session, projectid)
    if pd:

        ctx = create_build_ctx(pd, spec, version, settings.DOCKER_REGISTRY)

        sche = _get_scheduler()
        job = await run_async(sche.enqueue_build, ctx)

        return json(dict(msg="ok", execid=job.id), 202)
    return json(dict(msg="not found"), 404)


@projects_bp.post("/<projectid:str>/_upload", stream=True)
@openapi.parameter("version", str, "query")
@openapi.parameter("runtime", str, "query")
@protected()
async def project_upload(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument

    root = pathlib.Path(projectid)
    version = get_query_param2(request, "version", None)
    runtime_name = get_query_param2(request, "runtime", None)
    session = request.ctx.session
    async with session.begin():
        pd = await projects_mg.get_by_projectid(session, projectid)

    uri = build_upload_uri(pd.projectid, runtime_name, version)
    fileserver = f"{settings.FILESERVER}/{settings.FILESERVER_BUCKET}"
    dst_url = f"{fileserver}/{uri}"
    async with httpx.AsyncClient() as client:
        r = await client.put(dst_url, content=stream_reader(request))
    if r.status_code == 204:
        return empty()
    return json(dict(msg="ok"), r.status_code)


@projects_bp.get("/<projectid:str>/_private_key")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, "project")
@openapi.response(404, "not found")
@protected()
async def project_private_key(request, projectid):
    """Get private key based on the project"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    async with session.begin():
        r = await projects_mg.get_private_key(session, projectid)
        if r:
            return json({"private_key": r}, 200)

    return json(dict(msg="Not found"))
