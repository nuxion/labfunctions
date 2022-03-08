from sanic import Blueprint, Sanic

from nb_workflows.conf import defaults
from nb_workflows.conf.server_settings import settings
from nb_workflows.scheduler import SchedulerExecutor


def parse_page_limit(request, def_pg="1", def_lt="100"):
    strpage = request.args.get("page", [def_pg])
    strlimit = request.args.get("limit", [def_lt])
    page = int(strpage[0])
    limit = int(strlimit[0])

    return page, limit


def get_scheduler(qname=settings.RQ_CONTROL_QUEUE) -> SchedulerExecutor:

    current_app = Sanic.get_app(defaults.SANIC_APP_NAME)
    r = current_app.ctx.rq_redis
    return SchedulerExecutor(r, qname=qname)
