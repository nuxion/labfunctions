from nb_workflows.conf import defaults as df
from nb_workflows.executors import context as ctx
from nb_workflows.types import ProjectData
from tests import factories


def test_context_generate_execid():
    id_ = ctx.generate_execid()
    assert len(id_) == df.EXECID_LEN + len(ctx.steps.start) + 1
    assert isinstance(id_, str)


def test_context_pure_execid():
    id_ = ctx.generate_execid()
    pure = ctx.pure_execid(id_)
    assert "." not in pure
    assert len(pure) == df.EXECID_LEN


def test_context_move_step_execid():

    id_ = ctx.generate_execid()
    new_ = ctx.move_step_execid(ctx.steps.build, id_)
    assert ctx.steps.build in new_


def test_context_docker_name():
    pd = ProjectData(name="test", projectid="testid", owner="tester")
    dn = ctx.generate_docker_name(pd, "1.0")
    assert dn == "tester/test:1.0"


def test_context_create_notebook():
    pd = factories.ProjectDataFactory()
    # task = factories.NBTaskFactory()
    wd = factories.WorkflowDataWebFactory()

    id_ = ctx.generate_execid()
    pure = ctx.pure_execid(id_)
    execid = ctx.move_step_execid(ctx.steps.docker, id_)

    r = ctx.create_notebook_ctx(pd, wd, execid=execid)

    assert r.params.get("WFID")
    assert r.params.get("EXECUTIONID")
    assert r.params.get("NOW")
    assert r.output_name == f"{wd.nbtask.nb_name}.{pure}.ipynb"
