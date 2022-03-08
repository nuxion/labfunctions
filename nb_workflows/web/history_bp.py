# pylint: disable=unused-argument
from dataclasses import asdict

from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi
from sanic_jwt import protected

from nb_workflows.core.registers import register_history_db
from nb_workflows.managers import history_mg
from nb_workflows.types import ExecutionResult, HistoryRequest, NBTask
from nb_workflows.utils import get_query_param

history_bp = Blueprint("history", url_prefix="history")


@history_bp.get("/<jobid>")
@openapi.parameter("jobid", str, "path")
@openapi.response(200, "Found")
@openapi.response(404, dict(msg=str), "Not Found")
@openapi.parameter("lt", int, "lt")
@protected()
async def history_last_job(request, jobid):
    """Get the status of the last job executed"""
    # pylint: disable=unused-argument
    lt = get_query_param(request, "lt", 1)
    session = request.ctx.session
    async with session.begin():
        h = await history_mg.get_last(session, jobid, limit=lt)
        if h:
            return json(asdict(h), 200)

        return json(dict(msg="not found"), 404)


@history_bp.post("/")
@openapi.body({"application/json": HistoryRequest})
@openapi.response(201, "Created")
@protected()
async def history_create(request):
    """Register a jobexecution"""
    # pylint: disable=unused-argument

    dict_ = request.json
    task = NBTask(**dict_["task"])
    result = ExecutionResult(**dict_["result"])
    session = request.ctx.session
    async with session.begin():
        await register_history_db(session, result, task)
        await session.commit()

    return json(dict(msg="created"), 201)


@history_bp.post("/<projectid:str>/<jobid>/_output")
@openapi.parameter("jobid", str, "path")
@protected()
async def project_register_exec(request, projectid):
    """
    Upload a workflow project
    """
    # pylint: disable=unused-argument

    fsrv = AsyncFileserver(settings.FILESERVER)
    root = pathlib.Path(projectid / defaults.NB_OUTPUTS)

    data = request.form["result"][0]
    exec_task = ExecutionResult(**std_json.loads(data))

    file_body = request.files["file"][0].body

    fp = str(root / exec_task.output_name)
    await fsrv.put(fp, file_body)

    return json(dict(msg="OK"))
