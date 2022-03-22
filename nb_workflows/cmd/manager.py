import importlib
from getpass import getpass

import click
from alembic import command
from alembic.config import Config as AlembicConfig

from nb_workflows.conf import load_server
from nb_workflows.db.sync import SQL
from nb_workflows.managers import users_mg

settings = load_server()


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
        _u = input("username: ")
        _p = getpass()

        S = db.sessionmaker()
        with S() as session:
            u = users_mg.create_user(session, _u, _p, scopes, superuser, is_active=True)
            session.commit()

        click.echo(f"User {_u} created")

    elif action == "disable":
        S = db.sessionmaker()
        with S() as session:
            u = users_mg.disable_user(session, username)
            session.commit()
            if u:
                click.echo(f"{username} disabled")
            else:
                click.echo(f"{username} not found")

    elif action == "change-scopes":
        S = db.sessionmaker()
        with S() as session:
            u = users_mg.change_scopes(session, username, scopes)
            session.commit()
            if u:
                click.echo(f"{username} scopes changed")
            else:
                click.echo(f"{username} not found")

    elif action == "reset":
        S = db.sessionmaker()
        with S() as session:
            pm = users_mg.password_manager()
            u = users_mg.get_user(session, username)
            if u:
                _p = getpass()
                key = pm.encrypt(_p)
                u.password = key
                session.add(u)
                session.commit()
            else:
                click.echo("Invalid user...")

    else:
        click.echo("Wrong param...")


# managercli.add_command(db)
# managercli.add_command(users)
