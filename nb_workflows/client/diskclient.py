import getpass
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.panel import Panel

from nb_workflows import errors, secrets
from nb_workflows.conf import defaults
from nb_workflows.conf.jtemplates import render_to_file
from nb_workflows.types import (
    ExecutionResult,
    HistoryRequest,
    HistoryResult,
    NBTask,
    ProjectData,
    ProjectReq,
    ScheduleData,
    WorkflowData,
    WorkflowDataWeb,
    WorkflowsList,
)
from nb_workflows.utils import parse_var_line

from .base import BaseClient
from .history_client import HistoryClient
from .projects_client import ProjectsClient
from .types import Credentials, ProjectZipFile, WFCreateRsp
from .uploads import generate_dockerfile
from .utils import (
    get_credentials_disk,
    get_private_key,
    store_credentials_disk,
    store_private_key,
)
from .workflows_client import WorkflowsClient


def get_params_from_nb(nb_dict):
    params = {}
    for cell in nb_dict["cells"]:
        if cell["cell_type"] == "code":
            if cell["metadata"].get("tags"):
                _params = cell["source"]
                for p in _params:
                    try:
                        k, v = parse_var_line(p)
                        params.update({k: v})
                    except IndexError:
                        pass
    return params


def open_notebook(fp) -> Dict[str, Any]:
    with open(fp, "r", encoding="utf-8") as f:
        data = json.loads(f.read())
    return data


class DiskClient(WorkflowsClient, ProjectsClient, HistoryClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()

    def login(self, u: str, p: str, home_dir=defaults.CLIENT_HOME_DIR):
        super().login(u, p)
        store_credentials_disk(self.creds, home_dir)

    def logincli(self, home_dir=defaults.CLIENT_HOME_DIR):
        creds = get_credentials_disk(home_dir)
        if creds:
            self.creds = creds
        else:
            self.console.print(f"You are connecting to [magenta]{self._addr}[/magenta]")
            u = input("User: ")
            p = getpass.getpass("Password: ")
            self.login(u, p)

    def projects_private_key(self) -> str:
        """Gets private key to be shared to the docker container of a
        workflow task
        """
        r = self._http.get(f"/projects/{self.projectid}/_private_key")

        key = None
        if r.status_code == 200:
            key = r.json().get("private_key")
        if not key:
            raise errors.PrivateKeyNotFound(self.projectid)

        store_private_key(key, self.projectid)
        return key

    def projects_create(self) -> Union[ProjectData, None]:
        _key = secrets.generate_private_key()
        pq = ProjectReq(
            name=self.state.project.name,
            private_key=_key,
            projectid=self.state.project.projectid,
            description=self.state.project.description,
            repository=self.state.project.repository,
        )
        r = self._http.post(
            f"/projects",
            json=asdict(pq),
        )
        if r.status_code == 200:
            self.console.print("[bold yellow] Project already exist [/bold yellow]")
        elif r.status_code == 201:
            # self.console.print(p)
            pd = ProjectData(**r.json())
            store_private_key(_key, pd.projectid)
            return pd
        else:
            raise TypeError("Something went wrong creating the project %s", r.text)
        return None

    def projects_generate_dockerfile(self, docker_opts):
        root = Path.cwd()
        generate_dockerfile(root, docker_opts)

    def get_private_key(self) -> str:
        """shortcut for getting a private key locally
        TODO: separate command line cli from a general client and an agent client
        a command line cli has filesystem side effects and a agent client not"""
        key = get_private_key(self.projectid)
        if not key:
            return self.projects_private_key()
        return key

    @staticmethod
    def notebook_template(fp):
        render_to_file("test_workflow.ipynb.j2", fp)

    def create_workflow(self, nb_fullpath, alias):
        p = Path(nb_fullpath)
        if p.is_file():
            nb_dict = open_notebook(p)
            params = get_params_from_nb(nb_dict)
            if not params:
                self.logger.warning(f"Params not found for {nb_fullpath}")
        else:
            self.logger.warning(f"Notebook {nb_fullpath} not found, I will create one")
            self.notebook_template(nb_fullpath)

        nb_name = nb_fullpath.rsplit("/", maxsplit=1)[1].split(".")[0]

        task = NBTask(nb_name=nb_name, params=params)
        wd = WorkflowDataWeb(
            alias=alias,
            nbtask=task,
            enabled=False,
        )

        self.state.add_workflow(wd)
        self.write()

    def info(self):
        self.console.print(f"[bold]Project ID: [magenta]{self.projectid}[/][/]")
        self.console.print(f"[bold]Project Name: [blue]{self.project_name}[/][/]")
        # self.console.print(table)
