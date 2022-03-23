from nb_workflows.client import state

from .factories import NBTaskFactory, ProjectDataFactory, WorkflowDataWebFactory


def test_workflows_state_from_file():
    wf = state.from_file("tests/workflows_test.yaml")
    assert isinstance(wf, state.WorkflowsState)


def test_workflows_state_write(tempdir):
    wf = state.from_file("tests/workflows_test.yaml")
    wf.write(f"{tempdir}/workflows.yaml")
    wf_2 = state.from_file(f"{tempdir}/workflows.yaml")
    assert wf_2._project.name == wf._project.name


def test_workflows_state_file():
    wf = state.from_file("tests/workflows_test.yaml")
    wf2 = wf.file
    assert isinstance(wf2, state.WorkflowsFile)


def test_workflows_state_list2dict():
    tasks = WorkflowDataWebFactory.create_batch(size=5)
    res = state.WorkflowsState.listworkflows2dict(tasks)
    assert len(res.keys()) == 5


def test_workflows_state_add_workflow():
    pd = ProjectDataFactory()
    tasks = WorkflowDataWebFactory.create_batch(size=2)
    ws = state.WorkflowsState(pd, workflows={tasks[0].alias: tasks[0]})
    ws.add_workflow(tasks[1])
    assert len(ws.workflows.keys()) == 2
    assert tasks[1].alias in ws.workflows.keys()


def test_workflows_state_del_workflow():
    pd = ProjectDataFactory()
    tasks = WorkflowDataWebFactory.create_batch(size=2)
    tasks_dict = state.WorkflowsState.listworkflows2dict(tasks)
    ws = state.WorkflowsState(pd, workflows=tasks_dict)
    ws.delete_workflow(tasks[1].alias)
    assert len(ws.workflows.keys()) == 1
    assert tasks[1].alias not in ws.workflows.keys()


def test_workflows_state_update_prj():
    pd = ProjectDataFactory()
    wf = state.from_file("tests/workflows_test.yaml")
    wf.update_project(pd)
    assert wf.project.projectid == pd.projectid


# def test_workflows_file_seq(tempdir):
#     tmp = f"{tempdir}/workflows.yaml"
#     wf = workflows_file.from_file("tests/workflows_test.yaml")
#
#     spf = SeqPipeFactory()
#     wf.add_seq(spf)
#     wf.write(tmp)
#
#     seq = workflows_file.from_file(tmp)
#
#     assert len(wf._seq_pipes) == 1
#     assert seq._seq_pipes[0].alias == spf.alias
