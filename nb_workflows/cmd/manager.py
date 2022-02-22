from datetime import datetime
from getpass import getpass

import click
from sqlalchemy import select

from nb_workflows.auth import users as users_mgt
from nb_workflows.auth.models import GroupModel, UserModel
from nb_workflows.conf import Config
from nb_workflows.db.sync import SQL
from nb_workflows.utils import password_manager
from nb_workflows.workflows.models import HistoryModel, ScheduleModel


@click.group(chain=True)
def managercli():
    """
    wrapper
    """
    pass


@managercli.command()
@click.option("--sql", "-s", default=Config.SQL, help="SQL Database")
@click.argument("action", type=click.Choice(["create", "drop"]))
def db(sql, action):
    """Create or Drop tables from a database"""
    db = SQL(sql)
    if action == "create":
        db.create_all()
        click.echo("Created...")
    elif action == "drop":
        db.drop_all()
        click.echo("Droped...")
    else:
        click.echo("Wrong param...")


@managercli.command()
@click.option("--sql", "-s", default=Config.SQL, help="SQL Database")
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
            u = users_mgt.create_user(session, _u, _p, superuser, is_active=True)
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


managercli.add_command(db)
managercli.add_command(users)
