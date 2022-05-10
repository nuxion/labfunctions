import os
import secrets
from dataclasses import dataclass
from typing import Optional

from rich.console import Console

from labfunctions.commands import shell
from labfunctions.utils import get_free_port

console = Console()


@dataclass
class JupyterOpts:
    port: Optional[str] = None
    token: Optional[str] = None
    base_url: str = "/"
    addr: str = "127.0.0.1"


def check_jupyter_installed() -> bool:
    installed = False
    try:
        shell("jupyter --help", silent=True)
        installed = True
    except FileNotFoundError:
        pass
    return installed


def jupyter_exec(opts: JupyterOpts):

    port = opts.port or get_free_port(opts.addr)
    token = opts.token or secrets.token_urlsafe(50)
    env = os.environ
    env.update({"JUPYTER_TOKEN": token})
    is_local = os.environ.get("NB_LOCAL")
    installed = check_jupyter_installed()
    if not installed and not is_local:
        shell("pip install jupyterlab")
    elif not installed and is_local:
        console.log("[red bold](x) Jupyter lab is not installed[/]")

    console.print(
        f"=> Running jupyter into: [magenta bold]{opts.addr}:{port}{opts.base_url}[/]"
    )
    if is_local:
        console.print(f"Access token: {token}")

    cmd = (
        f"jupyter lab --ip={opts.addr}  --ServerApp.port={port} "
        f"--ServerApp.base_url={opts.base_url} "
        f"--no-browser "
        f"--ServerApp.shutdown_no_activity_timeout=15"
    )

    output = shell(cmd, env=env, silent=True)
