from pathlib import Path

from pytest_mock import MockerFixture

from nb_workflows import defaults
from nb_workflows.client import init_script
from nb_workflows.client.state import WorkflowsState
from nb_workflows.types import NBTask, WorkflowDataWeb
from nb_workflows.types.docker import DockerfileImage
from nb_workflows.utils import get_version


def test_init_script_example_task():
    t = init_script._example_task()

    assert isinstance(t, NBTask)
    assert t.nb_name == "welcome"


def test_init_script_example_workflow():
    t = init_script._example_workflow()

    assert isinstance(t, WorkflowDataWeb)
    assert t.enabled is False


def test_init_script_default_runtime(mocker: MockerFixture):
    root = Path(".")
    render_mock = mocker.patch(
        "nb_workflows.client.init_script.render_to_file", return_value=None
    )
    init_script._default_runtime(root)

    docker_name = render_mock.call_args_list[0][1]["data"]["version"]
    version = get_version()
    assert render_mock.called
    assert docker_name.startswith(defaults.DOCKERFILE_IMAGE)
    assert docker_name.endswith(version)


def test_init_script_empty_file(tempdir):
    ef = f"{tempdir}/test.txt"
    init_script._empty_file(ef)
    assert Path(ef).is_file()


def test_init_script_ask_prj(mocker: MockerFixture):
    mocker.patch("nb_workflows.client.init_script.Prompt.ask", return_value="demo test")
    name = init_script.ask_project_name()
    assert name == "demo_test"


def test_init_script_workflow_state(mocker: MockerFixture, tempdir):
    mocker.patch("nb_workflows.client.init_script.Prompt.ask", return_value="demo test")
    mocker.patch(
        "nb_workflows.client.init_script.WorkflowsState.write", return_value=None
    )
    state = init_script.workflow_state_init(
        Path(tempdir), "demo_test", projectid="test"
    )
    assert isinstance(state, WorkflowsState)
    assert state.project.name == "demo_test"
