from collections import OrderedDict
from typing import Dict, List, Optional, Union

import yaml

from nb_workflows.types import NBTask, ProjectData, WorkflowDataWeb
from nb_workflows.types.client import WorkflowsFile
from nb_workflows.types.docker import DockerfileImage
from nb_workflows.utils import Singleton, open_yaml, write_yaml


class WFDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(WFDumper, self).increase_indent(flow, False)


# class WorkflowsState(metaclass=Singleton):
class WorkflowsState:
    """This manage workflows state, is NOT Thread safe"""

    def __init__(
        self,
        project: Optional[ProjectData] = None,
        workflows: Optional[Dict[str, WorkflowDataWeb]] = None,
        runtime: Optional[DockerfileImage] = None,
        version="0.2.0",
    ):
        self._version = version
        self._project = project
        self._workflows = workflows or {}
        self._runtime = runtime

        self.snapshots: List[WorkflowsFile] = []

    @property
    def runtime(self) -> DockerfileImage:
        return self._runtime

    @property
    def projectid(self) -> Union[str, None]:
        if self.project:
            return self.project.projectid
        return None

    @property
    def project_name(self) -> Union[str, None]:
        if self.project:
            return self.project.name
        return None

    @staticmethod
    def listworkflows2dict(
        workflows: List[WorkflowDataWeb],
    ) -> Dict[str, WorkflowDataWeb]:
        _workflows = {w.alias: w for w in workflows}
        return _workflows

    def add_workflow(self, wf: WorkflowDataWeb):
        self._workflows.update({wf.alias: wf})

    def delete_workflow(self, alias):
        del self._workflows[alias]

    def find_by_id(self, wfid) -> Union[WorkflowDataWeb, None]:
        for alias in self._workflows:
            if self._workflows[alias].wfid == wfid:
                return self._workflows[alias]
        return None

    def update_project(self, pd: ProjectData):
        self._project = pd

    @property
    def file(self) -> WorkflowsFile:
        return WorkflowsFile(
            version=self._version,
            project=self._project,
            workflows=self._workflows,
            runtime=self._runtime,
        )

    @property
    def workflows(self) -> Dict[str, WorkflowDataWeb]:
        return self._workflows

    @property
    def project(self) -> ProjectData:
        return self._project

    def snapshot(self) -> WorkflowsFile:
        """
        It makes a deep copy of the workfile"
        """
        wf = self.file.copy(deep=True)

        # self.snapshots.append(wf)
        return wf

    @staticmethod
    def read(filepath="workflows.yaml") -> WorkflowsFile:
        # data_dict = open_toml(filepath)
        data_dict = open_yaml(filepath)

        wf = WorkflowsFile(**data_dict)
        return wf

    def write(self, fp="workflows.yaml"):
        """
        Writes the state to workflows.yaml (by default)
        Also perfoms some serializations
        """
        wf = self.snapshot()
        wf_dict = wf.dict()
        _dict = OrderedDict()
        _dict["version"] = wf.version
        _dict["project"] = wf.project.dict()
        if wf_dict.get("runtime"):
            _dict["runtime"] = wf.runtime.dict()
        if wf_dict.get("workflows"):
            _dict["workflows"] = {k: v.dict() for k, v in wf.workflows.items()}
        write_yaml(
            fp, dict(_dict), Dumper=WFDumper, default_flow_style=False, sort_keys=False
        )


def from_file(fpath="workflows.yaml") -> WorkflowsState:
    wf = WorkflowsState.read(fpath)
    return WorkflowsState(
        project=wf.project,
        version=wf.version,
        workflows=wf.workflows,
        runtime=wf.runtime,
    )
