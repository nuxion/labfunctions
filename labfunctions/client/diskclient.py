import getpass
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
from rich.console import Console
from rich.panel import Panel

from labfunctions import defaults, errors, secrets
from labfunctions.conf.jtemplates import render_to_file
from labfunctions.types import (
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
from labfunctions.utils import parse_var_line

from .base import BaseClient
from .history_client import HistoryClient
from .projects_client import ProjectsClient
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


console = Console()


class DiskClient(WorkflowsClient, ProjectsClient, HistoryClient, BaseClient):
    """Is to be used as cli client because it has side effects on local disk"""

    def __init__(self, *args, **kwargs):
        super(DiskClient, self).__init__(*args, **kwargs)
        self.console = Console()

    def login(self, u: str, p: str):
        super().login(u, p)
        store_credentials_disk(self.creds, self.homedir)

    def logincli(self):
        creds = get_credentials_disk(self.homedir)
        if creds:
            self.creds = creds
            rsp = self.verify()
            if rsp:
                return True
        self.creds = None
        console.print(f"You are connecting to [magenta]{self._addr}[/magenta]")
        u = input("User: ")
        p = getpass.getpass("Password: ")
        self.login(u, p)

    # def projects_private_key(self) -> str:
    #     """Gets private key to be shared to the docker container of a
    #     workflow task
    #     """
    #     try:
    #         r = self._http.get(f"/projects/{self.projectid}/_private_key")
    #     except httpx.ConnectError:
    #         raise errors.PrivateKeyNotFound(self.projectid)

    #     key = None
    #     if r.status_code == 200:
    #         key = r.json().get("private_key")
    #     if not key:
    #         raise errors.PrivateKeyNotFound(self.projectid)

    #     store_private_key(key, self.working_area)
    #     return key

    def get_private_key(self) -> str:
        """shortcut for getting a private key locally
        TODO: separate command line cli from a general client and an agent client
        a command line cli has filesystem side effects and a agent client not"""
        key = get_private_key(self.working_area)
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

    # def info(self):
    #    self.console.print(f"[bold]Project ID: [magenta]{self.projectid}[/][/]")
    #    self.console.print(f"[bold]Project Name: [blue]{self.project_name}[/][/]")
    # self.console.print(table)
