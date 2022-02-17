import click
import requests
import toml

from nb_workflows.conf import Config


def _open_toml(from_file: str):
    with open(from_file, "r") as f:
        tf = f.read()

    tomconf = toml.loads(tf)
    return tomconf


@click.command()
@click.option(
    "--from-file", "-f", default=None, help="toml file with the configuration"
)
@click.option("--web", default=Config.WORKFLOW_SERVICE, help="Web server")
def workflows(from_file, web):
    """Store workflows"""

    data = _open_toml(from_file)
    _workflows = data["workflow"]
    for w in _workflows:

        if w.get("interval"):
            rsp = requests.post(f"{web}/workflows/schedule/interval", json=w)
            d = rsp.json()
            code = rsp.status_code
        else:
            rsp = requests.post(f"{web}/workflows/schedule/cron", json=w)

            d = rsp.json()
            code = rsp.status_code
        if code == 201:
            click.echo(
                f"Inserted { w['task']['name'] } with id {d['jobid']}. {code}"
            )
        else:
            click.echo(
                f"Task { w['task']['name'] } with id {d['jobid']} already exist {code}"
            )
