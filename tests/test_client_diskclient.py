import json

from nb_workflows.client import diskclient as dc


def test_client_diskclient_params():
    with open("tests/workflow.ipynb", "r", encoding="utf-8") as f:
        nb_dict = json.loads(f.read())

    params = dc.get_params_from_nb(nb_dict)
    assert params.get("WFID") == "test_job"
    assert len(params.keys()) == 5


def test_client_diskclient_notebook_tmp(tempdir):
    dc.DiskClient.notebook_template(f"{tempdir}/test.ipynb")
    dict_ = dc.open_notebook(f"{tempdir}/test.ipynb")
    params = dc.get_params_from_nb(dict_)

    assert params.get("WFID") == "test_job"
    assert len(params.keys()) == 5
