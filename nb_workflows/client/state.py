from collections import OrderedDict
from typing import Dict, List, Optional

import yaml

from nb_workflows.types import NBTask, ProjectData, SeqPipe
from nb_workflows.types.client import Pipelines, WorkflowsFile
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
        workflows: Optional[Dict[str, NBTask]] = None,
        seqpipes: Optional[List[SeqPipe]] = None,
        version="0.2.0",
    ):
        self._version = version
        self._project = project
        self._seq_pipes = seqpipes or []
        self._workflows = workflows or {}

        self.snapshots: List[WorkflowsFile] = []

    @staticmethod
    def listworkflows2dict(workflows: List[NBTask]) -> Dict[str, NBTask]:
        _workflows = {w.alias: w for w in workflows}
        return _workflows

    def add_workflow(self, wf: NBTask):
        self._workflows.update({wf.alias: wf})

    def delete_workflow(self, alias):
        del self._workflows[alias]

    def add_seq(self, sp: SeqPipe):
        self._seq_pipes.append(sp)

    def update_project(self, pd: ProjectData):
        self._project = pd

    @property
    def file(self) -> WorkflowsFile:
        p = Pipelines(sequences=self._seq_pipes)
        return WorkflowsFile(
            version=self._version,
            project=self._project,
            # workflows={w.alias: w for w in self._workflows}
            workflows=self._workflows,
            pipelines=p,
        )

    @property
    def workflows(self) -> Dict[str, NBTask]:
        return self._workflows

    @property
    def project(self) -> ProjectData:
        return self._project

    def take_snapshot(self) -> WorkflowsFile:
        wf = self.file.copy(deep=True)

        breakpoint()
        # self.snapshots.append(wf)
        return wf

    @staticmethod
    def read(filepath="workflows.yaml") -> WorkflowsFile:
        # data_dict = open_toml(filepath)
        data_dict = open_yaml(filepath)

        wf = WorkflowsFile(**data_dict)
        return wf

    def write(self, fp="workflows.yaml"):
        """Order to be dumped to a yaml file"""
        wf = self.file
        wf_dict = wf.dict()
        pipes = wf_dict.get("pipelines")
        _dict = OrderedDict()
        _dict["version"] = wf.version
        _dict["project"] = wf.project.dict()
        _dict["workflows"] = wf_dict.get("workflows")
        _dict["pipelines"] = wf_dict.get("pipelines")
        write_yaml(
            fp, dict(_dict), Dumper=WFDumper, default_flow_style=False, sort_keys=False
        )


def from_file(fpath="workflows.yaml") -> WorkflowsState:
    wf = WorkflowsState.read(fpath)
    pipes = wf.pipelines
    seq = None
    if wf.pipelines:
        seq = pipes.sequences

    return WorkflowsState(
        project=wf.project,
        version=wf.version,
        workflows=wf.workflows,
        seqpipes=seq,
    )