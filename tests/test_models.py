from redislite import Redis
from rq import Queue
from sqlalchemy import select

from nb_workflows import scheduler
from nb_workflows.models import HistoryModel, WorkflowModel
from nb_workflows.types import NBTask, ScheduleData

from .factories import WorkflowDataWebFactory

# def test_models_history(connection, session):
#     h = history_factory(session)()
#     session.add(h)
#     session.commit()
#     assert h.id == 0


def test_models_workflows(connection, session):

    wfd = WorkflowDataWebFactory()
    wm = WorkflowModel(
        alias=wfd.alias,
        nbtask=wfd.nbtask.dict(),
        schedule=wfd.schedule.dict(),
    )

    session.add(wm)
    session.flush()
    stmt = select(WorkflowModel).where(WorkflowModel.alias == wfd.alias)
    row = session.execute(stmt)

    r = row.scalar_one_or_none()
    assert isinstance(r, WorkflowModel)
    assert r.alias == wfd.alias
