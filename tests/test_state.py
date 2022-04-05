from nb_workflows.client.state import WorkflowsState

from .factories import (
    DockerfileImageFactory,
    ProjectDataFactory,
    WorkflowDataWebFactory,
)


def test_state_WorkflowsState():
    pd = ProjectDataFactory()
    wd = WorkflowDataWebFactory()
    di = DockerfileImageFactory()

    wf = WorkflowsState(project=pd, workflows={wd.alias: wd}, runtime=di)

    wd_find = wf.find_by_id(wd.wfid)
    not_found = wf.find_by_id("not found")

    assert isinstance(wf, WorkflowsState)
    assert wf.runtime.image == di.image
    assert wf.project_name == pd.name
    assert wd_find.wfid == wd.wfid
    assert not_found is None
