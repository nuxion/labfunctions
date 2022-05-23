import pytest

from labfunctions import types
from labfunctions.client.labstate import LabState

from .factories import (
    DockerfileImageFactory,
    ProjectDataFactory,
    WorkflowDataWebFactory,
)


def test_client_labstate_LabState():
    pd = ProjectDataFactory()
    wd = WorkflowDataWebFactory()
    wd2 = WorkflowDataWebFactory()

    lf = LabState(project=pd, workflows={wd.alias: wd})
    name = lf.project_name
    filepath = lf.filepath
    file_ = lf.file
    workflows = lf.workflows
    workflows_dict = lf.listworkflows2dict([wd])

    lf2 = LabState(project=pd, workflows={wd.alias: wd})
    lf2._project = None
    not_projectid = lf2.projectid
    not_name = lf2.project_name
    with pytest.raises(AttributeError):
        lf2.projectid = "invalid"

    wd_find = lf.find_by_id(wd.wfid)
    not_found = lf.find_by_id("not found")

    lf.add_workflow(wd2)

    assert wd2.alias in lf.workflows.keys()
    assert isinstance(lf, LabState)
    assert lf.project_name == pd.name
    assert wd_find.wfid == wd.wfid
    assert not_found is None
    assert not_projectid is None
    assert not_name is None
    assert name == pd.name
    assert isinstance(file_, types.Labfile)
    assert isinstance(workflows, dict)
    assert isinstance(workflows_dict, dict)


def test_client_labstate_write(tempdir):
    wf = LabState.from_file("tests/labfile_test.yaml")
    wf.write(f"{tempdir}/workflows.yaml")
    wf_2 = LabState.from_file(f"{tempdir}/workflows.yaml")
    assert wf_2._project.name == wf._project.name


def test_client_labstate_file():
    wf = LabState.from_file("tests/labfile_test.yaml")
    wf2 = wf.file
    assert isinstance(wf2, types.Labfile)


def test_client_labstate_list2dict():
    tasks = WorkflowDataWebFactory.create_batch(size=5)
    res = LabState.listworkflows2dict(tasks)
    assert len(res.keys()) == 5


def test_client_labstate_add_workflow():
    pd = ProjectDataFactory()
    tasks = WorkflowDataWebFactory.create_batch(size=2)
    ws = LabState(pd, workflows={tasks[0].alias: tasks[0]})
    ws.add_workflow(tasks[1])
    assert len(ws.workflows.keys()) == 2
    assert tasks[1].alias in ws.workflows.keys()


def test_client_labstate_del_workflow():
    pd = ProjectDataFactory()
    tasks = WorkflowDataWebFactory.create_batch(size=2)
    tasks_dict = LabState.listworkflows2dict(tasks)
    ws = LabState(pd, workflows=tasks_dict)
    ws.delete_workflow(tasks[1].alias)
    assert len(ws.workflows.keys()) == 1
    assert tasks[1].alias not in ws.workflows.keys()


def test_client_labstate_update_prj():
    pd = ProjectDataFactory()
    wf = LabState.from_file("tests/labfile_test.yaml")
    wf.update_project(pd)
    assert wf.project.projectid == pd.projectid
