import json
import os
import sys
from pathlib import Path
from typing import List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn

from labfunctions import defaults, types
from labfunctions.client.diskclient import DiskClient
from labfunctions.utils import format_bytes, mkdir_p, open_toml, write_toml

console = Console()
progress = Progress(
    SpinnerColumn(),
    "[progress.description]{task.description}",
)


class ConfigCli:
    def __init__(self):
        self.homedir = Path.home().resolve()
        self.data = self.open()
        self.write()

    @staticmethod
    def open() -> types.config.ConfigCliType:
        homedir = Path.home().resolve()
        fullconf = f"{defaults.CLIENT_HOME_DIR}/{defaults.CLIENT_CONFIG_CLI}"
        try:
            _conf = open_toml(f"{homedir / fullconf}")
            conf = types.config.ConfigCliType(**_conf)
        except FileNotFoundError:
            url = os.environ.get(defaults.SERVICE_URL_ENV, defaults.SERVICE_URL)
            conf = types.config.ConfigCliType(url_service=url)
        return conf

    def write(self):
        homedir = Path.home().resolve()
        fullconf = homedir / defaults.CLIENT_HOME_DIR / defaults.CLIENT_CONFIG_CLI
        mkdir_p(homedir / defaults.CLIENT_HOME_DIR)

        write_toml(fullconf.resolve(), self.data.dict())

    def set(self, key, value):
        setattr(self.data, key, value)
        self.write()

    def get(self, key):
        return getattr(self.data, key)

    def list(self) -> List[str]:
        return list(self.data.dict().keys())


def watcher(c: DiskClient, execid, stats=False):
    keep = True
    last = None

    console = Console()
    console.print(f"[bold magenta]Watching for execid: {execid}[/]")
    events = 0

    for evt in c.events_listen(execid, last=last):
        if evt.event == "stats" and stats:
            _stats = json.loads(evt.data)
            _mem = _stats["mem"]["mem_usage"]
            mem = format_bytes(_mem)
            msg = f"[orange]Memory used {mem}[/]"
            console.print(msg)
        elif evt.event == "result":
            keep = False
            console.print(f"[bold green]Finished execid: [/] [bold magenta]{execid}[/]")
        elif evt.event != "stats":
            msg = evt.data
            console.print(msg)
        last = evt.id
        events += 1


def create_secrets_certs(pubkey_path, privkey_path):
    from labfunctions.commands import shell

    base_path = Path(privkey_path).resolve().parent

    if not Path(privkey_path).is_file():
        mkdir_p(base_path)
        res = shell(
            (f"openssl ecparam -genkey -name secp521r1 -noout " f"-out {privkey_path}"),
            check=False,
        )
        if res.returncode != 0:
            console.print(f"[red]{res.stderr}[/]")
            sys.exit(-1)
        res = shell(
            (f"openssl ec -in {privkey_path} -pubout " f"-out {pubkey_path}"),
            check=False,
        )
        if res.returncode != 0:
            console.print(f"[red]{res.stderr}[/]")
            sys.exit(-1)

        console.print("=> Secrets created")
    else:
        console.print("=> Keys already exist")
