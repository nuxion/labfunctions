class CommandExecutionException(Exception):
    def __init__(self, message):
        super().__init__(message)


class WorkflowDisabled(Exception):
    def __init__(self, projectid, jobid):
        _msg = f"projectid: {projectid} and jobid: {jobid} disabled"
        super().__init__(_msg)


class WorkflowNotFound(Exception):
    def __init__(self, projectid, jobid):
        _msg = f"projectid: {projectid} and jobid: {jobid} not found"
        super().__init__(_msg)


class ProjectNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)
