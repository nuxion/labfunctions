from dataclasses import asdict

from discord_webhook import DiscordWebhook

from nb_workflows.conf import Config
from nb_workflows.db.sync import SQL
from nb_workflows.workflows.models import HistoryModel

_EMOJI_ERROR = "🤬"
_EMOJI_OK = "👌"


def send_discord_error(msg):
    txt = f"{_EMOJI_ERROR} - {msg}"
    webhook = DiscordWebhook(url=Config.DISCORD_EVENTS, content=txt)
    webhook.execute()


def send_discord_ok(msg):
    txt = f"{_EMOJI_OK} - {msg}"
    webhook = DiscordWebhook(url=Config.DISCORD_EVENTS, content=txt)
    webhook.execute()


def rq_job_ok(job, connection, result, *args, **kwargs):
    """callback for RQ"""
    db = SQL(Config.SQL)

    result_data = asdict(result)

    status = 0
    if result.error:
        send_discord_error(msg=f"{result.taskid} failed. {result.error}")
        status = -1
    row = HistoryModel(
        taskid=job.id,
        # jobid=result.alias,
        name=result.name,
        result=result_data,
        status=status,
    )
    session = db.sessionmaker()()
    session.add(row)
    session.commit()
    session.close()


def rq_job_error(job, connection, type, value, traceback):
    """callback for RQ"""
    db = SQL(Config.SQL)

    data = dict(value=str(value), type=str(type), traceback=str(traceback))
    name = "error"
    if job.params:
        name = job.params[0].get("name", name)

    row = HistoryModel(taskid=job.id, name=name, result=data, status=-2)
    session = db.sessionmaker()()
    session.add(row)
    session.commit()
    session.close()

    send_discord_error(msg=f"{job.id} failed. {name}")


def job_history_register(task_result, nb_task):
    """run inside of the nb_job_executor"""
    db = SQL(Config.SQL)

    result_data = asdict(task_result)

    status = 0
    if task_result.error:
        status = -1
        send_discord_error(
            msg=f"{task_result.taskid} failed. { task_result.name }"
        )

    row = HistoryModel(
        taskid=task_result.taskid,
        jobid=nb_task.jobid,
        name=task_result.name,
        result=result_data,
        status=status,
    )
    session = db.sessionmaker()()
    session.add(row)
    session.commit()
    session.close()

    if nb_task.notificate and status == 0:
        send_discord_ok(msg=f"{task_result.taskid} finished ok")
