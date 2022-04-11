from nb_workflows.conf.server_settings import settings
from nb_workflows.control_plane import rqscheduler


def test_rqscheduler_run(mocker):
    mocker.patch(
        "nb_workflows.control_plane.rqscheduler.Scheduler.run", return_value=None
    )
    rqscheduler.run(settings.RQ_REDIS, 5, "INFO")
