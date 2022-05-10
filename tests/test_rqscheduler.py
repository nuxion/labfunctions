from labfunctions.conf.server_settings import settings
from labfunctions.control_plane import rqscheduler


def test_rqscheduler_run(mocker):
    mocker.patch(
        "labfunctions.control_plane.rqscheduler.Scheduler.run", return_value=None
    )
    rqscheduler.run(settings.RQ_REDIS, 5, "INFO")
