# pylint: disable=unused-argument
import pathlib
from dataclasses import asdict
from typing import List, Union

# import aiofiles
from sanic import Blueprint, Sanic, exceptions
from sanic.response import json
from sanic_ext import openapi
from sanic_jwt import inject_user, protected

from nb_workflows.auth import get_auth
from nb_workflows.auth.types import UserData
from nb_workflows.client.types import Credentials
from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.io import AsyncFileserver
from nb_workflows.managers import projects_mg
from nb_workflows.scheduler import SchedulerExecutor
from nb_workflows.types import ProjectData, ProjectReq
from nb_workflows.utils import run_async, secure_filename

projects_bp = Blueprint("projects", url_prefix="projects")


async def generate_id(session, retries=3) -> Union[str, None]:
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


@projects_bp.get("/_generateid")
@openapi.response(200, "project")
@openapi.response(500, "not found")
async def project_generateid(request):
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
@inject_user()
@protected()
async def project_create(request, user: UserData):
    """Create a new project"""
    # pylint: disable=unused-argument

    dict_ = request.json
    pd = ProjectReq(**dict_)
    session = request.ctx.session
    r = await projects_mg.create(session, user.user_id, pd)
    if r:
        d_ = r.to_dict(
            rules=(
                "-id",
                "-private_key",
                "-created_at",
                "-updated_at",
                "-user",
                "-user_id",
            )
        )
        return json(d_, 201)
    return json(dict(msg="already exist"), 200)


@projects_bp.put("/")
@openapi.body({"application/json": ProjectReq})
@openapi.response(202, "created")
@protected()
@inject_user()
async def project_create_or_update(request, user: UserData):
    """Create or update a project"""
    # pylint: disable=unused-argument

    dict_ = request.json
    pd = ProjectReq(**dict_)
    session = request.ctx.session
    r = await projects_mg.create_or_update(session, user.user_id, pd)
    return json(dict(msg="created"), 202)


@projects_bp.get("/")
@openapi.response(200, List[ProjectData], "project-list")
@protected()
@inject_user()
async def project_list(request, user: UserData):
    """Get a list of projects belonging to a user"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    result = await projects_mg.list_all(session, user.user_id)
    return json([r.dict() for r in result], 200)


@projects_bp.get("/<projectid:str>")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, "project")
@openapi.response(404, "not found")
@protected()
@inject_user()
async def project_get_one(request, projectid, user: UserData):
    """Get one project"""
    # pylint: disable=unused-argument

    session = request.ctx.session
    # async with session.begin():
    r = await projects_mg.get_by_projectid(session, projectid, user_id=user.user_id)
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


@projects_bp.post("/<projectid:str>/_agent_token")
@openapi.parameter("projectid", str, "path")
@openapi.response(200, Credentials, "agent credentials")
@protected()
@inject_user()
async def project_create_agent_token(request, projectid, user: UserData):
    """
    Create an agent token
    TODO: create an special user to be used as agent
    """
    # pylint: disable=unused-argument
    _auth = get_auth()
    # default is 30 min
    with _auth.override(expiration_delta=(60 * 60) * 12):
        token = await _auth.generate_access_token(user)
        refresh = await _auth.generate_refresh_token(request, asdict(user))

    return json(dict(access_token=token, refresh_token=refresh), 200)


@projects_bp.post("/<projectid:str>/_upload")
@protected()
async def project_upload(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument

    # root = pathlib.Path(settings.BASE_PATH)
    # (root / settings.WF_UPLOADS).mkdir(parents=True, exist_ok=True)
    fsrv = AsyncFileserver(settings.FILESERVER)
    root = pathlib.Path(settings.WF_UPLOADS)
    file_body = request.files["file"][0].body
    name = secure_filename(request.files["file"][0].name)
    fp = str(root / projectid / name)
    await fsrv.put(fp, file_body)

    sche = _get_scheduler()

    job = await run_async(sche.enqueue_build, projectid, fp)

    # fp = str(root / settings.WF_UPLOADS / name)
    # async with aiofiles.open(fp, "wb") as f:
    #    await f.write(file_body)

    return json(dict(msg="ok", jobid=job.id), 201)
