from nb_workflows.client import workflows_file as wf
from tests.factories import NBTaskFactory, ProjectDataFactory

pd = ProjectDataFactory()
t = NBTaskFactory()
t2 = NBTaskFactory()
t3 = NBTaskFactory()

ws = wf.WorkflowsState(project=pd, workflows=[t, t2, t3])
ws.write("workflows.example.yaml")
