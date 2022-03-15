import click

from nb_workflows.conf import load_server
from nb_workflows.utils import init_blueprints

settings = load_server()


@click.group()
def servicescli():
    """
    wrapper
    """
    pass


@servicescli.command()
@click.option("--host", "-H", default="0.0.0.0", help="Listening Host")
@click.option("--port", "-p", default="8000", help="Listening Port")
@click.option("--workers", "-w", default=1, help="How many workers start?")
@click.option(
    "--apps",
    "-a",
    default="workflows,projects,history",
    help="List of apps to be mounted as blueprints",
)
@click.option(
    "--auto-reload", "-A", default=False, is_flag=True, help="Enable Auto reload"
)
@click.option(
    "--access-log", "-L", default=False, is_flag=True, help="Enable access_log"
)
@click.option("--debug", "-D", default=False, is_flag=True, help="Enable Auto reload")
def web(host, port, workers, apps, auto_reload, access_log, debug):
    """Run web server"""
    # pylint: disable=import-outside-toplevel
    from nb_workflows.server import app

    list_bp = apps.split(",")
    init_blueprints(app, list_bp)
    w = int(workers)
    print("Debug mode: ", debug)
    app.run(
        host=host,
        port=int(port),
        workers=w,
        auto_reload=auto_reload,
        debug=debug,
        access_log=access_log,
    )


@servicescli.command()
@click.option("--host", "-H", default=settings.RQ_REDIS_HOST, help="Redis host")
@click.option("--port", "-p", default=settings.RQ_REDIS_PORT, help="Redis port")
@click.option("--db", "-d", default=settings.RQ_REDIS_DB, help="Redis DB")
@click.option(
    "--interval", "-i", default=60, help="How often the scheduler checks for work"
)
@click.option("--log-level", "-L", default="INFO")
def rqscheduler(host, port, db, interval, log_level):
    """Run RQ scheduler"""
    # pylint: disable=import-outside-toplevel
    from redis import Redis
    from rq_scheduler.scheduler import Scheduler
    from rq_scheduler.utils import setup_loghandlers

    connection = Redis(host, port, db)
    setup_loghandlers(log_level)
    scheduler = Scheduler(connection=connection, interval=interval)
    scheduler.run()


@servicescli.command()
@click.option("--workers", "-w", default=2, help="How many workers spawn")
@click.option(
    "--qnames",
    "-q",
    default="default",
    help="Comma separated list of queues to listen to",
)
def rqworker(workers, qnames):
    """Run RQ worker"""
    # pylint: disable=import-outside-toplevel
    from nb_workflows.qworker import run_workers

    # from nb_workflows.conf import defaults
    # queues = [defaults. for q in qnames.split(",")]

    run_workers(qnames.split(","), workers)


# servicescli.add_command(manager)
servicescli.add_command(web)
servicescli.add_command(rqscheduler)
servicescli.add_command(rqworker)
