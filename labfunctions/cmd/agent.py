import os
import sys

import click

from labfunctions.conf.server_settings import settings
from labfunctions.control_plane import rqscheduler
from labfunctions.types.agent import AgentConfig
from labfunctions.utils import get_external_ip, get_hostname

hostname = get_hostname()


@click.group(name="agent")
def agentcli():
    """
    Execute agent related actions
    """
    pass


@agentcli.command(name="run")
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
    help="Cluster name, it will be added as qname",
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
def runcli(redis, workers, qnames, cluster, ip_address, agent_name, machine_id):
    """Run the agent"""
    # pylint: disable=import-outside-toplevel
    from labfunctions.control_plane import agent

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


@click.command(name="scheduler")
@click.option("--redis", "-r", default=settings.RQ_REDIS, help="Redis full dsn")
@click.option(
    "--interval", "-i", default=60, help="How often the scheduler checks for work"
)
@click.option("--log-level", "-L", default="INFO")
def rqschedulercli(redis, interval, log_level):
    """Run RQ scheduler"""
    # pylint: disable=import-outside-toplevel
    rqscheduler.run(redis, interval, log_level)
