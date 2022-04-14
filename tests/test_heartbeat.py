import time

from nb_workflows.control_plane import heartbeat


def test_heartbeat_run(redis):
    ht = heartbeat.HeartbeatThread(redis, name="test")
    ht.setDaemon(True)
    ht.start()
    time.sleep(0.3)
    key = redis.get("nb.ag.heart.test")
    ht.unregister()
    time.sleep(0.3)
    not_key = redis.get("nb.ag.heart.test")

    assert not_key is None
    assert key == b"alive"
