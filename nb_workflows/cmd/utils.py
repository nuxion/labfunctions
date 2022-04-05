import json

from rich.console import Console

from nb_workflows.client.diskclient import DiskClient
from nb_workflows.utils import format_bytes


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
