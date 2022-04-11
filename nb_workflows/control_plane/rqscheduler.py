import redis
from rq_scheduler.scheduler import Scheduler
from rq_scheduler.utils import setup_loghandlers


def run(redis_dsn, interval, log_level):
    connection = redis.from_url(redis_dsn)
    setup_loghandlers(log_level)
    scheduler = Scheduler(connection=connection, interval=interval)
    scheduler.run()
