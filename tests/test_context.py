from nb_workflows.executors import context as ctx
from nb_workflows.types import ProjectData
from tests import factories


def test_context_generate_execid():
    id_ = ctx.generate_execid(10)
    assert len(id_) == 10
    assert isinstance(id_, str)


def test_context_execid_from_scheduler():
    id_ = ctx.execid_from_scheduler(size=10)
    assert len(id_) == 10 + 4
    assert id_.startswith("SCH")


def test_context_docker_name():
    pd = ProjectData(name="test", projectid="testid", username="tester")
    dn = ctx.generate_docker_name(pd, "1.0")
    assert dn == "tester/test:1.0"


def test_context_create_notebook():
    pd = factories.ProjectDataFactory()
    task = factories.NBTaskFactory()

    execid = "testid"
    r = ctx.create_notebook_ctx(pd, task, execid=execid)

    assert r.params.get("JOBID")
    assert r.params.get("EXECUTIONID")
    assert r.params.get("NOW")
    assert r.output_name == f"{task.nb_name}.{execid}.ipynb"
