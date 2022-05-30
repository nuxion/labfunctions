import os
import sys
from pathlib import Path

import click

from labfunctions.conf.server_settings import settings
from labfunctions.types.agent import AgentConfig
from labfunctions.utils import get_external_ip, get_hostname, mkdir_p

from .utils import console, create_secrets_certs

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
@click.option(
    "--init-secrets",
    "-I",
    default=False,
    is_flag=True,
    help="Create certs for auth system",
)
@click.option("--debug", "-D", default=False, is_flag=True, help="Enable Auto reload")
def webcli(host, port, workers, apps, auto_reload, access_log, debug, init_secrets):
    """Run API Web Server"""
    # pylint: disable=import-outside-toplevel
    from labfunctions.server import create_app

    if init_secrets:
        create_secrets_certs(
            settings.SECURITY.JWT_PUBLIC, settings.SECURITY.JWT_PRIVATE
        )
    console.print("BASE PATH: ", settings.BASE_PATH)

    list_bp = apps.split(",")
    app = create_app(settings, list_bp)
    w = int(workers)
    console.print("Debug mode: ", debug)
    app.run(
        host=host,
        port=int(port),
        workers=w,
        auto_reload=auto_reload,
        debug=debug,
        access_log=access_log,
    )
