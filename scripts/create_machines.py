from rich.console import Console

from nb_workflows.conf import load_server
from nb_workflows.db.sync import SQL
from nb_workflows.managers import machine_mg
from nb_workflows.types.cluster import MachineOrm
from nb_workflows.utils import open_yaml

console = Console()

settings = load_server()
db = SQL(settings.SQL)
Session = db.sessionmaker()


data = open_yaml("scripts/machines.yaml")

with Session() as session:
    for name, machine in data["machines"].items():
        m = MachineOrm(**machine)
        console.print(
            f"Adding [magenta bold]{name}[/] for provider [magenta bold]{m.provider}[/]"
        )
        machine_mg.create_or_update_sync(session, m)

    session.commit()
