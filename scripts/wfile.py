from nb_workflows.client import state as wf
from tests.factories import NBTaskFactory, ProjectDataFactory

pd = ProjectDataFactory()
tasks = NBTaskFactory.create_batch(3)
tasks_dict = wf.WorkflowsState.listworkflows2dict(tasks)

ws = wf.WorkflowsState(project=pd, workflows=tasks_dict)
ws.write("workflows.example.yaml")
