import importlib
import sys
from getpass import getpass

import click
from alembic import command
from alembic.config import Config as AlembicConfig
from rich.console import Console
from rich.prompt import Confirm, Prompt

from nb_workflows.conf import load_server
from nb_workflows.db.sync import SQL
from nb_workflows.managers import users_mg
from nb_workflows.types.user import UserOrm

settings = load_server()
console = Console()


@click.group(name="manager")
def managercli():
    """
    Managment tasks like user creation and db init
    """
    pass


def alembic_ugprade(dburi, to="head"):
    alembic_cfg = AlembicConfig("nb_workflows/db/alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", dburi)
    command.upgrade(alembic_cfg, to)


@managercli.command()
@click.option("--sql", "-s", default=settings.SQL, help="SQL Database")
@click.argument("action", type=click.Choice(["create", "drop", "upgrade"]))
def db(sql, action):
    """Create or Drop tables from a database"""
    db = SQL(sql)
    settings.SQL = sql
    # auth_mod = importlib.import_module("nb_workflows.auth.models")
    wf_mod = importlib.import_module("nb_workflows.models")

    if action == "create":
        db.create_all()
        click.echo("Created...")
    elif action == "drop":
        db.drop_all()
        click.echo("Droped...")
    elif action == "upgrade":
        alembic_ugprade(sql)
    else:
        click.echo("Wrong param...")


@managercli.command()
@click.option("--sql", "-s", default=settings.SQL, help="SQL Database")
@click.option(
    "--superuser", "-S", is_flag=True, default=False, help="User as supersuer"
)
@click.option("--scopes", default="user", help="User scopes")
@click.option("--username", "-u", default=None, help="Username")
@click.argument(
    "action", type=click.Choice(["create", "disable", "reset", "change-scopes"])
)
def users(sql, superuser, scopes, username, action):
    """Manage users"""
    db = SQL(sql)
    if action == "create":
        name = Prompt.ask("Username")
        email = Prompt.ask("Email (optional)", default=None)
        password = getpass("Password: ")
        repeat = getpass("Password (repeat): ")
        if password != repeat:
            console.print("[bold red]Paswords doesn't match[/]")
            sys.exit(-1)

        S = db.sessionmaker()
        with S() as session:
            obj = UserOrm(
                username=name,
                # password=key,
                email=email,
                is_active=True,
                scopes=scopes,
                is_superuser=superuser,
            )
            user = users_mg.create(
                session, obj, password=password, salt=settings.SECURITY.AUTH_SALT
            )
            session.commit()
        console.print(f"[bold magenta]Congrats!! user {name} created")

    elif action == "disable":
        S = db.sessionmaker()
        with S() as session:
            u = users_mg.disable_user(session, username)
            session.commit()
            if u:
                click.echo(f"{username} disabled")
            else:
                click.echo(f"{username} not found")

    # elif action == "change-scopes":
    #     S = db.sessionmaker()
    #     with S() as session:
    #         u = users_mg.change_scopes(session, username, scopes)
    #         session.commit()
    #         if u:
    #             click.echo(f"{username} scopes changed")
    #         else:
    #             click.echo(f"{username} not found")

    elif action == "reset":
        name = Prompt.ask("Username")
        _p = getpass("Password: ")
        S = db.sessionmaker()
        with S() as session:
            changed = users_mg.change_pass(
                session, name, _p, salt=settings.SECURITY.AUTH_SALT
            )
            session.commit()
        if changed:
            console.print("[bold magenta]Pasword changed[/]")
        else:
            console.print("[bold red]User may not exist [/]")
    else:
        console.print("[red bold]Wrongs params[/]")


# managercli.add_command(db)
# managercli.add_command(users)
