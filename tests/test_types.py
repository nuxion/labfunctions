from nb_workflows.models import ProjectModel
from nb_workflows.types import NBTask, ProjectData, ScheduleData

from .factories import NBTaskFactory, ScheduleDataFactory


def test_types_projectmodel2data():
    pm = ProjectModel(
        projectid="testid",
        name="test name",
        private_key="private",
        description="desc",
        repository="http://test",
        user_id=1,
    )
    pd = ProjectData.from_orm(pm)
    assert isinstance(pd, ProjectData)


def test_types_nbtask_serialization():
    sd = ScheduleDataFactory()
    nb = NBTaskFactory()
    nb.schedule = sd
    dict_ = nb.dict()
    assert dict_["schedule"]["repeat"] == sd.repeat


def test_types_nbtask_deserialization():
    sd = ScheduleDataFactory()
    nb = NBTaskFactory()
    nb.schedule = sd
    dict_ = nb.dict()
    task = NBTask(**dict_)
    assert isinstance(task.schedule, ScheduleData)
