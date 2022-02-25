import os
import pathlib
from datetime import datetime
from getpass import getpass

import click
from alembic import command
from alembic.config import Config as AlembicConfig
from nb_workflows.auth import users as users_mgt
from nb_workflows.auth.models import GroupModel, UserModel
from nb_workflows.conf import settings
from nb_workflows.conf.jtemplates import render_to_file
from nb_workflows.db.sync import SQL
from nb_workflows.utils import password_manager
from nb_workflows.workflows import client
from nb_workflows.workflows.models import HistoryModel, ScheduleModel
from sqlalchemy import select


@click.group(chain=True)
def managercli():
    """
    wrapper
    """
    pass


def alembic_ugprade(dburi, to="head"):
    alembic_cfg = AlembicConfig('nb_workflows/db/alembic.ini')
    alembic_cfg.set_main_option('sqlalchemy.url', dburi)
    command.upgrade(alembic_cfg, to)


@managercli.command()
@click.option("--sql", "-s", default=settings.SQL, help="SQL Database")
@click.argument("action", type=click.Choice(["create", "drop", "upgrade"]))
def db(sql, action):
    """Create or Drop tables from a database"""
    db = SQL(sql)
    settings.SQL = sql
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
@click.option("--username", "-u", default=None, help="Username")
@click.argument("action", type=click.Choice(["create", "disable", "reset"]))
def users(sql, superuser, username, action):
    """Manage users"""

    db = SQL(sql)
    if action == "create":
        _u = input("username: ")
        _p = getpass()

        S = db.sessionmaker()
        with S() as session:
            u = users_mgt.create_user(
                session, _u, _p, superuser, is_active=True)
            session.commit()

        click.echo(f"User {_u} created")

    elif action == "disable":
        S = db.sessionmaker()
        with S() as session:
            u = users_mgt.disable_user(session, username)
            session.commit()
            if u:
                click.echo(f"{username} disabled")
            else:
                click.echo(f"{username} not found")

    elif action == "reset":
        S = db.sessionmaker()
        with S() as session:
            pm = password_manager()
            u = users_mgt.get_user(session, username)
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


@managercli.command()
@click.option("--create-dirs", "-C", is_flag=True, default=True,
              help="Create outpus and workflows dir")
@click.argument("base_path")
def startproject(base_path, create_dirs):
    """Start a new project """
    p = pathlib.Path(f"{base_path}/nb_app")
    print("="*60)
    print(f" Starting project in {p.resolve()} ")
    print("="*60)
    print()

    p.mkdir(parents=True, exist_ok=True)
    root = pathlib.Path(base_path)
    render_to_file("settings.py.j2", str((p / "settings.py").resolve()))
    if settings.DOCKER_OPTIONS:
        print(f" Dockerfile created")
        render_to_file("Dockerfile", str((root / "Dockerfile").resolve()),
                       data=settings.DOCKER_OPTIONS)

    if settings.DOCKER_COMPOSE:
        print(f" docker-compose created")
        render_to_file("docker-compose.yml",
                       str((root / "docker-compose.yml").resolve()),
                       data=settings.DOCKER_COMPOSE)

    print(f" Makefile added")
    render_to_file("Makefile", str((root / "Makefile").resolve()))
    print(f" .gitignore added")
    render_to_file("gitignore", str((root / ".gitignore").resolve()))

    with open(p / "__init__.py", "w") as f:
        pass

    if create_dirs:
        print(f" outputs/ and workflows/ dir created")
        (root / "outputs").mkdir(parents=True, exist_ok=True)
        (root / "workflows").mkdir(parents=True, exist_ok=True)

    w_conf = client.init(settings.WORKFLOW_SERVICE)
    w_conf.write(str(root / "workflows.example.toml"))

    print("\n Next steps: ")
    print("\n\t1. init a git repository")
    print("\t2. create a workflow inside of the workflows folder")
    print("\t3. publish your work")
    print()


managercli.add_command(db)
managercli.add_command(users)
managercli.add_command(startproject)
