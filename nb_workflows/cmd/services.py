import os
import sys

import click

from nb_workflows.conf.server_settings import settings
from nb_workflows.types.agent import AgentConfig
from nb_workflows.utils import get_external_ip, get_hostname

hostname = get_hostname()


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
    "--cluster",
    "-C",
    default="default",
    help="Cluster name, also it will be added as qname",
)
@click.option(
    "--ip-address",
    "-i",
    default=None,
    help="IP address of the host",
)
@click.option(
    "--agent-name",
    "-a",
    default=None,
    help="Agent Name",
)
@click.option("--machine-id", "-m", default=f"localhost/ba/{hostname}")
def agentcli(redis, workers, qnames, cluster, ip_address, agent_name, machine_id):
    """Run the agent"""
    # pylint: disable=import-outside-toplevel
    from nb_workflows.control_plane import agent

    sys.path.append(settings.BASE_PATH)
    os.environ["NB_AGENT_TOKEN"] = settings.AGENT_TOKEN
    os.environ["NB_AGENT_REFRESH_TOKEN"] = settings.AGENT_REFRESH_TOKEN
    os.environ["NB_WORKFLOW_SERVICE"] = settings.WORKFLOW_SERVICE
    ip_address = ip_address or get_external_ip(settings.DNS_IP_ADDRESS)
    queues = qnames.split(",")

    conf = AgentConfig(
        redis_dsn=redis,
        cluster=cluster,
        qnames=queues,
        ip_address=ip_address,
        machine_id=machine_id,
        heartbeat_ttl=settings.AGENT_HEARTBEAT_TTL,
        heartbeat_check_every=settings.AGENT_HEARTBEAT_CHECK,
        agent_name=agent_name,
        workers_n=workers,
    )

    agent.run(conf)
