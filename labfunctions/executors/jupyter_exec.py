import json
import os
import secrets
import sys
from dataclasses import asdict, dataclass
from subprocess import CompletedProcess
from typing import Any, Dict, Optional

from rich.console import Console

from labfunctions import defaults
from labfunctions.commands import DockerCommand, shell
from labfunctions.hashes import generate_random
from labfunctions.utils import get_free_port

console = Console()


@dataclass
class JupyterCtx:
    addr: str
    port: Optional[str] = None
    token: Optional[str] = None
    base_url: str = "/"

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

    def str_json(self):
        return json.dumps(self.dict())

    def set_env(self):
        ctx_str = self.str_json()
        os.environ[defaults.JUPYTERCTX_VAR] = ctx_str

    @staticmethod
    def from_env() -> "JupyterCtx":
        ctx_str = os.getenv(defaults.JUPYTERCTX_VAR)
        return JupyterCtx(**json.loads(ctx_str))


@dataclass
class JupyterResult:
    messages: str
    error: bool = False

    @staticmethod
    def from_command(output: CompletedProcess) -> "JupyterResult":
        error = False
        messages = ""
        if output.returncode != 0:
            error = True
        if output.stderr:
            messages += output.stderr.decode("utf-8")
        if output.stdout:
            messages += output.stdout.decode("utf-8")
        return JupyterResult(
            messages=messages,
            error=error,
        )


def create_jupyter_ctx(addr: str = "127.0.0.1") -> JupyterCtx:

    random_url = generate_random(alphabet=defaults.NANO_URLSAFE_ALPHABET)
    port = get_free_port(addr)
    token = secrets.token_urlsafe(50)
    ctx = JupyterCtx(addr=addr, base_url=f"/{random_url}", token=token, port=port)
    return ctx


def check_jupyter_installed() -> bool:
    installed = True
    res = shell("jupyter lab --help", silent=True, check=False)
    if res.returncode != 0:
        installed = False
    return installed


def jupyter_docker_exec(addr: str, docker_image: str):
    cmd = DockerCommand()
    ctx = create_jupyter_ctx(addr=addr)

    console.print(f"=> URL: {ctx.addr}:{ctx.port}{ctx.base_url}")
    console.print(f"=> Token: {ctx.token}")

    result = cmd.run(
        f"lab exec jupyter --addr {addr} --docker",
        docker_image,
        network_mode="host",
        env_data={defaults.JUPYTERCTX_VAR: ctx.str_json()},
    )
    return result


def jupyter_exec(install_jupyter=True) -> JupyterResult:
    ctx = JupyterCtx.from_env()
    env = os.environ
    env.update({"JUPYTER_TOKEN": ctx.token})

    installed = check_jupyter_installed()
    if not installed and install_jupyter:
        shell("pip install jupyterlab")
    elif not installed and not install_jupyter:
        console.print("[red bold](x) Jupyter lab is not installed[/]")
        sys.exit(-1)

    console.print(
        f"=> Running jupyter into: [magenta bold]{ctx.addr}:{ctx.port}{ctx.base_url}[/]"
    )
    console.print(f"Access token: {ctx.token}")

    cmd = (
        f"jupyter lab --ip={ctx.addr}  --ServerApp.port={ctx.port} "
        f"--ServerApp.base_url={ctx.base_url} "
        f"--no-browser "
        f"--ServerApp.shutdown_no_activity_timeout=15"
    )

    output = shell(cmd, env=env, silent=True, check=False)
    result = JupyterResult.from_command(output)

    return result
