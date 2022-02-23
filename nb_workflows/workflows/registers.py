from dataclasses import asdict

from discord_webhook import DiscordWebhook
from nb_workflows.conf import Config
from nb_workflows.db.sync import SQL
from nb_workflows.workflows.entities import ExecutionResult, NBTask
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
        send_discord_error(msg=f"{result.executionid} failed. {result.error}")
        status = -1
    row = HistoryModel(
        executionid=job.id,
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

    row = HistoryModel(executionid=job.id, name=name, result=data, status=-2)
    session = db.sessionmaker()()
    session.add(row)
    session.commit()
    session.close()

    send_discord_error(msg=f"{job.id} failed. {name}")


def job_history_register(execution_result: ExecutionResult,
                         nb_task: NBTask):
    """run inside of the nb_job_executor"""
    db = SQL(Config.SQL)

    result_data = asdict(execution_result)

    status = 0
    if execution_result.error:
        status = -1

    row = HistoryModel(
        jobid=nb_task.jobid,
        executionid=execution_result.executionid,
        elapsed_secs=execution_result.elapsed_secs,
        nb_name=execution_result.name,
        result=result_data,
        status=status,
    )
    session = db.sessionmaker()()
    session.add(row)
    session.commit()
    session.close()

    if status == 0 and nb_task.notifications_ok:
        # send_notification
        # send_discord_ok(msg=f"{execution_result.executionid} finished ok")
        pass
    if status != 0 and nb_task.notifications_fail:
        # send_discord_error(
        #    msg=f"{execution_result.executionid} failed. { execution_result.name }"
        # )
        # send notification
        pass
