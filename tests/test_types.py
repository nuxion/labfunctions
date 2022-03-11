from nb_workflows.models import ProjectModel
from nb_workflows.types import ProjectData


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
