from collections import OrderedDict
from typing import Dict, List, Optional, Union

from labfunctions import defaults, types
from labfunctions.utils import IndentDumper, open_yaml, write_yaml


class LabState:
    """This manage workflows state, is NOT Thread safe"""

    def __init__(
        self,
        project: Optional[types.ProjectData] = None,
        workflows: Optional[Dict[str, types.WorkflowDataWeb]] = None,
        version=defaults.LABFILE_VER,
        lab_file: Optional[str] = None,
    ):
        self._version = version
        self._project = project
        self._workflows = workflows or {}
        self._file = lab_file

    @classmethod
    def from_file(cls, fpath=defaults.LABFILE_NAME) -> "LabState":
        wf = LabState.read(fpath)
        return cls(
            project=wf.project,
            version=wf.version,
            workflows=wf.workflows,
            lab_file=fpath,
        )

    @property
    def filepath(self) -> Union[str, None]:
        return self._file

    @property
    def projectid(self) -> Union[str, None]:
        if self.project:
            return self.project.projectid
        return None

    @projectid.setter
    def projectid(self, projectid):
        if not self.project:
            raise AttributeError("No project property")
        self.project.projectid = projectid

    @property
    def project_name(self) -> Union[str, None]:
        if self.project:
            return self.project.name
        return None

    @property
    def file(self) -> types.Labfile:
        return types.Labfile(
            version=self._version,
            project=self._project,
            workflows=self._workflows,
            # runtime=self._runtime,
        )

    @property
    def workflows(self) -> Dict[str, types.WorkflowDataWeb]:
        return self._workflows

    @property
    def project(self) -> types.ProjectData:
        return self._project

    @staticmethod
    def listworkflows2dict(
        workflows: List[types.WorkflowDataWeb],
    ) -> Dict[str, types.WorkflowDataWeb]:
        _workflows = {w.alias: w for w in workflows}
        return _workflows

    def add_workflow(self, wf: types.WorkflowDataWeb):
        self._workflows.update({wf.alias: wf})

    def delete_workflow(self, alias):
        del self._workflows[alias]

    def find_by_id(self, wfid) -> Union[types.WorkflowDataWeb, None]:
        for alias in self._workflows:
            if self._workflows[alias].wfid == wfid:
                return self._workflows[alias]
        return None

    def update_project(self, pd: types.ProjectData):
        self._project = pd

    def snapshot(self) -> types.Labfile:
        """
        It makes a deep copy of the workfile"
        """
        lf = self.file.copy(deep=True)

        # self.snapshots.append(wf)
        return lf

    @staticmethod
    def read(filepath=defaults.LABFILE_NAME) -> types.Labfile:
        # data_dict = open_toml(filepath)
        data_dict = open_yaml(filepath)

        lf = types.Labfile(**data_dict, workflows_file=filepath)
        return lf

    def write(self, fp=defaults.LABFILE_NAME):
        """
        Writes the state to workflows.yaml (by default)
        Also perfoms some serializations
        """
        wf = self.snapshot()
        wf_dict = wf.dict(exclude_none=True)
        _dict = OrderedDict()
        _dict["version"] = wf.version
        _dict["project"] = wf.project.dict(exclude_none=True)
        # if wf_dict.get("runtime"):
        #    _dict["runtime"] = wf.runtime.dict(exclude_none=True)
        if wf_dict.get("workflows"):
            _dict["workflows"] = {
                k: v.dict(exclude_none=True, exclude_unset=True)
                for k, v in wf.workflows.items()
            }
        write_yaml(
            fp,
            dict(_dict),
            Dumper=IndentDumper,
            default_flow_style=False,
            sort_keys=False,
        )
