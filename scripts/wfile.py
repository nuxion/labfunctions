from labfunctions.client import state as wf
from tests.factories import (
    DockerfileImageFactory,
    NBTaskFactory,
    ProjectDataFactory,
    WorkflowDataWebFactory,
)

pd = ProjectDataFactory()
workflows = WorkflowDataWebFactory.create_batch(3)
tasks_dict = wf.WorkflowsState.listworkflows2dict(workflows)
runtime = DockerfileImageFactory()

ws = wf.WorkflowsState(project=pd, workflows=tasks_dict, runtime=runtime)
ws.write("workflows.example.yaml")
