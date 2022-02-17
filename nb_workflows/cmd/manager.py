import click

from nb_workflows.conf import Config
from nb_workflows.db.sync import SQL
from nb_workflows.workflows.models import HistoryModel, ScheduleModel


@click.command()
@click.option("--sql", "-s", default=Config.SQL, help="SQL Database")
@click.argument("action", type=click.Choice(["createdb", "dropdb"]))
def manager(sql, action):
    """Create or Drop all tables from a database"""
    db = SQL(sql)
    if action == "createdb":
        db.create_all()
        click.echo("Created...")
    elif action == "dropdb":
        db.drop_all()
        click.echo("Droped...")
    else:
        click.echo("Wrong param...")
