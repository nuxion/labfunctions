from rich.console import Console

from labfunctions.conf import load_server
from labfunctions.db.sync import SQL
from labfunctions.managers import machine_mg
from labfunctions.types.cluster import MachineOrm
from labfunctions.utils import open_yaml

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
