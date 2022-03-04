from nb_workflows.conf import settings
from nb_workflows.core.managers import workflows


def make_worker_dirs():
    pass

def worker_exec(projectid, jobid):
    db = SQL(settings.SQL)
    Session = db.sessionmaker()

    with Session() as session:
        wd = workflows.get_by_jobid(session, jobid)
        
    

    nb_client = client.from_file("workflows.toml")
    try:
        rsp = nb_client.get_workflow(jobid)
        if rsp and rsp.enabled:
            exec_res = nb_job_executor(rsp.task)
            nb_client.register_history(exec_res, rsp.task)

            return exec_res
        elif not rsp.task:
            nb_client.rq_cancel_job(jobid)
        else:
            print(f"{jobid} not enabled")
    except KeyError:
        print("Invalid credentials")
    except TypeError:
        print("Somenthing went wrong")
    return None
