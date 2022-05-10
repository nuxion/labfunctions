import importlib
import sys
from getpass import getpass

import click
from alembic import command
from alembic.config import Config as AlembicConfig
from rich import print_json
from rich.console import Console
from rich.prompt import Confirm, Prompt

from nb_workflows.conf import load_server
from nb_workflows.db.sync import SQL
from nb_workflows.managers import projects_mg, users_mg
from nb_workflows.security import auth_from_settings
from nb_workflows.security.redis_tokens import RedisTokenStore
from nb_workflows.server import create_web_redis
from nb_workflows.types.user import UserOrm
from nb_workflows.utils import run_sync

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


@managercli.command()
@click.option("--sql", "-s", default=settings.SQL, help="SQL Database")
@click.option("--scopes", default="agent:r:w", help="agent scopes")
@click.option("--username", "-u", default=None, help="Agent username")
@click.option("--admin", "-A", default=False, is_flag=True, help="Agent as admin")
@click.option("--exp", "-e", default=30, help="Expire time")
@click.argument("action", type=click.Choice(["create", "get-token", "delete"]))
def agent(sql, scopes, username, action, admin, exp):
    db = SQL(sql)
    store = RedisTokenStore(settings.WEB_REDIS)
    auth = auth_from_settings(settings.SECURITY, store=store)

    if action == "create":
        S = db.sessionmaker()
        with S() as session:
            um = run_sync(
                projects_mg.create_agent, session, scopes=scopes, is_admin=admin
            )
            jwt = run_sync(users_mg.get_jwt_token, auth, um, exp)
            session.commit()
            print_json(
                data={
                    "username": um.username,
                    "scopes": um.scopes.split(","),
                    "jwt": jwt.dict(),
                }
            )
    elif action == "get-token":
        if not username:
            console.print("[bold red]A username should be given[/]")
            return
        S = db.sessionmaker()
        with S() as session:
            um = users_mg.get_user(session, username)
            if not um:
                console.print("[bold red]Username not found[/]")
                return
            jwt = run_sync(users_mg.get_jwt_token, auth, um, exp)
            print_json(
                data={
                    "username": um.username,
                    "scopes": um.scopes.split(","),
                    "jwt": jwt.dict(),
                }
            )

    elif action == "delete":
        if not username:
            console.print("[bold red]A username should be given[/]")
            return
        S = db.sessionmaker()
        with S() as session:
            users_mg.delete_user(session, username)
            session.commit()
        console.print("[bold green]Agent deleted[/]")


@managercli.command()
def shell():
    """starts a IPython REPL console with db objects and models"""
    from IPython import start_ipython

    db = SQL(settings.SQL)
    Session = db.sessionmaker()
    start_ipython(
        argv=[],
        user_ns={
            "settings": settings,
            "Session": Session,
            "db": db,
            "session": Session(),
        },
    )


# managercli.add_command(db)
# managercli.add_command(users)
