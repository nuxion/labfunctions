from nb_workflows.workflows import scheduler
from nb_workflows.workflows.entities import NBTask, ScheduleData
from nb_workflows.workflows.models import HistoryModel, ScheduleModel
from redislite import Redis
from rq import Queue

from .factories import history_factory, schedule_factory

nb_task_simple = NBTask(
    nb_name="test_workflow",
    params={"TIMEOUT": 1},
)


def test_workflows_historymodel(connection, session):
    h = history_factory(session)()
    session.add(h)
    session.commit()
    assert h.id == 0


def test_workflows_schedulemodel(connection, session):

    sched = schedule_factory(session)()

    session.add(sched)
    session.commit()
    assert sched.id == 0


def test_workflows_get_job_from_db(connection, session):
    sched = schedule_factory(session)()
    obj = scheduler.get_job_from_db(session, sched.jobid)
    assert isinstance(obj, ScheduleModel)


def test_workflows_QueueExecutor(redis):
    q = scheduler.QueueExecutor(redis=redis, is_async=False)

    assert isinstance(q.Q, Queue)


def test_workflows_enqueue_nb(redis):
    q = scheduler.QueueExecutor(redis=redis, is_async=False)

    j = q.enqueue_notebook(nb_task_simple)
    j2 = q.fetch_job(j.id)
    assert j.id == j2.id
    assert j.is_finished
