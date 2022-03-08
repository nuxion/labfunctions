from redislite import Redis
from rq import Queue

from nb_workflows import scheduler
from nb_workflows.models import HistoryModel, WorkflowModel
from nb_workflows.types import NBTask, ScheduleData

from .factories import history_factory, workflow_factory

nb_task_simple = NBTask(
    nb_name="test_workflow",
    params={"TIMEOUT": 1},
)


def test_models_history(connection, session):
    h = history_factory(session)()
    session.add(h)
    session.commit()
    assert h.id == 0


def test_models_workflows(connection, session):

    wf_model = workflow_factory(session)()

    session.add(wf_model)
    session.commit()
    assert wf_model.id == 0
