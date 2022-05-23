# pylint: disable=unused-argument
import json as std_json
import pathlib
from typing import List, Union

import httpx
from sanic import Blueprint, Request, Sanic, exceptions
from sanic.response import empty, json
from sanic_ext import openapi

from labfunctions import defaults, types
from labfunctions.conf.server_settings import settings
from labfunctions.defaults import API_VERSION
from labfunctions.managers import projects_mg, users_mg
from labfunctions.runtimes.context import build_upload_uri, create_build_ctx
from labfunctions.security import get_auth
from labfunctions.security.web import protected
from labfunctions.utils import run_async, secure_filename
from labfunctions.web.utils import (
    get_kvstore,
    get_query_param2,
    get_scheduler2,
    stream_reader,
)

projects_bp = Blueprint("projects", url_prefix="projects", version=API_VERSION)


def get_token_data(request: Request):
    return request.ctx.token_data


@projects_bp.post("/")
@openapi.body({"application/json": types.ProjectReq})
@openapi.response(201, types.ProjectData, "Created")
@protected()
@users_mg.inject_user
async def project_create(request, user: types.user.UserOrm):
    """Create a new project"""
    # pylint: disable=unused-argument

    dict_ = request.json
    token_data = get_token_data(request)
    pr = types.ProjectReq(**dict_)
    session = request.ctx.session
    r = await projects_mg.create(session, user.id, pr)
    if r:
        return json(r.dict(), 201)
    return json(dict(msg="already exist"), 200)


@projects_bp.put("/")
@openapi.body({"application/json": types.ProjectReq})
@openapi.response(202, "created")
@protected()
@users_mg.inject_user
async def project_create_or_update(request, user: types.user.UserOrm):
    """Create or update a project"""
    # pylint: disable=unused-argument

    dict_ = request.json
    pd = types.ProjectReq(**dict_)
    session = request.ctx.session
    async with session() as new_session:
        r = await projects_mg.create_or_update(new_session, user.id, pd)
    return json(dict(msg="created"), 202)


@projects_bp.get("/")
@openapi.response(200, List[types.ProjectData], "project-list")
@protected()
@users_mg.inject_user
async def project_list(request, user: types.user.UserOrm):
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
async def project_get_one(request, projectid, user: types.user.UserOrm):
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
        res = await projects_mg.create_agent(session, projectid)
        if res:
            return json(dict(msg=res.username), 201)

    return json(dict(msg="not created"), 200)


@projects_bp.delete("/<projectid:str>/agent/<agentname:str>")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("agentname", str, "path")
@protected()
async def project_delete_user_agent(request, projectid, agentname):
    """
    Delete a User Agent
    """
    session = request.ctx.session
    await projects_mg.delete_agent(session, agentname, projectid)
    await session.commit()
    return json(dict(msg="deleted"), 200)


@projects_bp.post("/<projectid:str>/agent/_token")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, types.user.AgentJWTResponse, "agent credentials")
@protected()
async def project_get_last_agent_token(request, projectid: str):
    """
    Get the agent token by a project
    """
    # pylint: disable=unused-argument
    _auth = get_auth(request)
    session = request.ctx.session
    # redis = request.ctx.web_redis

    agt = await projects_mg.get_agent_project(session, projectid)
    if agt:
        jwt = await users_mg.get_jwt_token(_auth, agt, exp=settings.AGENT_TOKEN_EXP)
        agt_jwt = types.user.AgentJWTResponse(agent_name=agt.username, creds=jwt)
        return json(agt_jwt.dict(), 200)
    return json({"msg": "agent not found"}, 404)


@projects_bp.post("/<projectid:str>/agent/<agent:str>/_token")
@openapi.parameter("projectid", str, "path")
@openapi.parameter("agent", str, "path")
@openapi.response(200, types.user.AgentJWTResponse, "agent credentials")
@protected()
async def project_get_agent_token(request, projectid: str, agent: str):
    """
    Get the agent token by a project
    """
    # pylint: disable=unused-argument
    _auth = get_auth(request)
    session = request.ctx.session
    redis = request.ctx.web_redis

    agt = await projects_mg.get_agent(session, agent, projectid)
    jwt = await users_mg.get_jwt_token(_auth, agt, exp=settings.AGENT_TOKEN_EXP)
    agt_jwt = types.user.AgentJWTResponse(agent_name=agt.username, creds=jwt)

    return json(agt_jwt.dict(), 200)


@projects_bp.get("/<projectid:str>/agent")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, List[str], "agent credentials")
@protected()
async def project_agents_list(request, projectid: str):
    """
    Get the agent token by a project
    """
    # pylint: disable=unused-argument
    session = request.ctx.session

    agents = await projects_mg.get_agent_list(session, projectid)

    return json(agents, 200)


@projects_bp.post("/<projectid:str>/_build")
@openapi.body({"application/json": types.RuntimeSpec})
@openapi.parameter("version", str, "query")
@openapi.body({"application/json": types.runtimes.BuildCtx})
@protected()
async def project_build(request, projectid):
    """
    Enqueue docker build image
    """
    # pylint: disable=unused-argument
    spec = types.RuntimeSpec(**request.json)
    version = get_query_param2(request, "version", None)
    scheduler = get_scheduler2(request)
    session = request.ctx.session
    ctx = await scheduler.enqueue_build(
        session, runtime=spec, projectid=projectid, version=version
    )

    return json(ctx.dict(), 202)


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

    kv = get_kvstore(request)
    rsp = await kv.put_stream(uri, stream_reader(request))
    if rsp:
        return json(dict(msg="ok"), 201)
    else:
        return empty()

    # fileserver = f"{settings.FILESERVER}/{settings.FILESERVER_BUCKET}"
    # dst_url = f"{fileserver}/{uri}"
    # async with httpx.AsyncClient() as client:
    #    r = await client.put(dst_url, content=stream_reader(request))
    # if r.status_code == 204:
    #    return empty()


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
