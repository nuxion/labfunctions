from nb_workflows.client import workflows_file

from .factories import SeqPipeFactory


def test_workflows_file_from_file():
    wf = workflows_file.from_file("tests/workflows_test.yaml")
    assert isinstance(wf, workflows_file.WorkflowsState)
    assert wf._project.name == "test"


def test_workflows_file_write(tempdir):
    wf = workflows_file.from_file("tests/workflows_test.yaml")
    wf.write(f"{tempdir}/workflows.yaml")
    wf_2 = workflows_file.from_file(f"{tempdir}/workflows.yaml")
    assert wf_2._project.name == "test"


def test_workflows_file_add_seq():
    wf = workflows_file.from_file("tests/workflows_test.yaml")
    spf = SeqPipeFactory()
    wf.add_seq(spf)
    assert len(wf._seq_pipes) == 1
    assert wf._seq_pipes[0].alias == spf.alias


def test_workflows_file_file():
    wf = workflows_file.from_file("tests/workflows_test.yaml")
    wf2 = wf.file
    assert isinstance(wf2, workflows_file.WorkflowsFile)


def test_workflows_file_seq(tempdir):
    tmp = f"{tempdir}/workflows.yaml"
    wf = workflows_file.from_file("tests/workflows_test.yaml")

    spf = SeqPipeFactory()
    wf.add_seq(spf)
    wf.write(tmp)

    seq = workflows_file.from_file(tmp)

    assert len(wf._seq_pipes) == 1
    assert seq._seq_pipes[0].alias == spf.alias
