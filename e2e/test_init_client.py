import time

import invoke
import pytest
from invoke import Responder
from sqlalchemy import inspect, select

from nb_workflows.auth import users
from nb_workflows.auth.models import UserModel
from nb_workflows.db.sync import SQL

from . import tester

CLIENT_ENV = ".env.dev.dockerclient"


def sql_query(ipaddr, envs):
    data = {e.split("=")[0]: e.split("=")[1] for e in envs}
    user = data["POSTGRES_USER"]
    pass_ = data["POSTGRES_PASSWORD"]
    dbname = data["POSTGRES_DB"]

    return f"postgresql://{user}:{pass_}@{ipaddr}:5432/{dbname}"


def get_tables(db):
    inspector = inspect(db.engine)
    tables = inspector.get_table_names(schema="public")
    return tables


@pytest.fixture(scope="module")
def docker_runner():
    dr = tester.DockerRunner.from_env()
    dr.clean()
    dr.create_network("workflows")
    dr.run_postgres()
    dr.run_redis()
    # TODO: check readynness
    time.sleep(4)
    yield dr
    dr.clean()


@pytest.fixture(scope="module")
def db_session(docker_runner):
    envs = docker_runner.open_env_file(".env.dev.docker")
    ipaddr = docker_runner.get_ip("postgres")
    dsl = sql_query(ipaddr, envs)
    _db = SQL(dsl)
    _db.create_all()
    Session = _db.sessionmaker()

    yield Session


@pytest.fixture(scope="module")
def webserver(db_session, docker_runner):

    rsp, id_ = docker_runner.run_on_server("nb web", daemon=True)
    envs = docker_runner.open_env_file(".env.dev.docker")
    envs_dict = tester.envs2dict(envs)
    envs_dict["NB_WORKFLOW_SERVICE"] = f"http://{id_}:8000"
    tester.write_envsdict(CLIENT_ENV, envs_dict)
    yield id_
    docker_runner.rm_docker(rsp.stdout.strip())


def test_cli_create_db(docker_runner: tester.DockerRunner):

    tables = [
        "nb_auth_user",
        "nb_project",
        "nb_auth_user_groups",
        "nb_auth_group",
        "nb_projects_users",
        "nb_history",
        "nb_workflow",
    ]
    tables_set = set(tables)
    envs = docker_runner.open_env_file(".env.dev.docker")
    envs.append("NB_SERVER=True")

    output, _ = docker_runner.run_on_server("nb db create")

    ipaddr = docker_runner.get_ip("postgres")
    dsl = sql_query(ipaddr, envs)
    db = SQL(dsl)
    tables = get_tables(db)

    assert len(tables_set.difference(set(tables))) == 0
    assert "Created" in output.stdout
    assert output.exited == 0


def test_cli_create_user(db_session, docker_runner: tester.DockerRunner):
    rsp_user = Responder(pattern=r"username: ", response="nuxion\n")
    rsp_pass = Responder(pattern=r"Password: ", response="meolvide\n")

    rsp, _ = docker_runner.run_on_server(
        "nb users create", tty=True, watchers=[rsp_user, rsp_pass]
    )

    with db_session() as session:
        u = users.get_user(session, "nuxion")

    assert rsp.exited == 0
    assert u


def test_cli_webserver(docker_runner):
    rsp, _ = docker_runner.run_on_server("nb web", daemon=True)

    # debug
    # id_ = rsp.stdout.strip()
    # logs = invoke.run(f"docker logs {id_}")

    docker_runner.rm_docker(rsp.stdout.strip())
    assert rsp.exited == 0


def test_cli_login(docker_runner, webserver):
    rsp_user = Responder(pattern=r"User: ", response="nuxion\n")
    rsp_pass = Responder(pattern=r"Password: ", response="meolvide\n")

    rsp = docker_runner.run_on_client(
        "nb login", tty=True, watchers=[rsp_user, rsp_pass], env_file=CLIENT_ENV
    )

    assert rsp.exited == 0
