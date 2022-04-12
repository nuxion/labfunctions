import os
import sys

import click

from nb_workflows.conf import load_server
from nb_workflows.utils import get_external_ip

settings = load_server()


@click.command(name="web")
@click.option("--host", "-H", default="0.0.0.0", help="Listening Host")
@click.option("--port", "-p", default="8000", help="Listening Port")
@click.option("--workers", "-w", default=1, help="How many workers start?")
@click.option(
    "--apps",
    "-a",
    default="workflows,projects,history,events,runtimes",
    help="List of apps to be mounted as blueprints",
)
@click.option(
    "--auto-reload", "-A", default=False, is_flag=True, help="Enable Auto reload"
)
@click.option(
    "--access-log", "-L", default=False, is_flag=True, help="Enable access_log"
)
@click.option("--debug", "-D", default=False, is_flag=True, help="Enable Auto reload")
def webcli(host, port, workers, apps, auto_reload, access_log, debug):
    """Run API Web Server"""
    # pylint: disable=import-outside-toplevel
    from nb_workflows.server import create_app

    list_bp = apps.split(",")
    app = create_app(settings, list_bp)
    w = int(workers)
    print("Debug mode: ", debug)
    app.run(
        host=host,
        port=int(port),
        workers=w,
        auto_reload=auto_reload,
        debug=debug,
        access_log=access_log,
    )


@click.command(name="rqscheduler")
@click.option("--redis", "-r", default=settings.RQ_REDIS, help="Redis full dsn")
@click.option(
    "--interval", "-i", default=60, help="How often the scheduler checks for work"
)
@click.option("--log-level", "-L", default="INFO")
def rqschedulercli(redis, interval, log_level):
    """Run RQ scheduler"""
    # pylint: disable=import-outside-toplevel
    from nb_workflows.control_plane import rqscheduler

    rqscheduler.run(redis, interval, log_level)


@click.command(name="agent")
@click.option("--workers", "-w", default=1, help="How many workers spawn")
@click.option("--redis", "-r", default=settings.RQ_REDIS, help="Redis full dsn")
@click.option(
    "--qnames",
    "-q",
    default="default",
    help="Comma separated list of queues to listen to",
)
@click.option(
    "--ip-address",
    "-i",
    default=None,
    help="IP address of the host",
)
@click.option(
    "--worker-name",
    "-W",
    default=None,
    help="Worker Name",
)
def agentcli(redis, workers, qnames, ip_address, worker_name):
    """Run N RQ workers"""
    # pylint: disable=import-outside-toplevel
    from nb_workflows.control_plane import agent

    sys.path.append(settings.BASE_PATH)
    os.environ["NB_AGENT_TOKEN"] = settings.AGENT_TOKEN
    os.environ["NB_AGENT_REFRESH_TOKEN"] = settings.AGENT_REFRESH_TOKEN
    os.environ["NB_WORKFLOW_SERVICE"] = settings.WORKFLOW_SERVICE
    ip_address = ip_address or get_external_ip(settings.DNS_IP_ADDRESS)

    agent.run(
        redis,
        qnames.split(","),
        name=worker_name,
        ip_address=ip_address,
        workers_n=workers,
    )
