class CommandExecutionException(Exception):
    def __init__(self, message):
        super().__init__(message)


class WorkflowDisabled(Exception):
    def __init__(self, projectid, wfid):
        _msg = f"projectid: {projectid} and wfid: {wfid} disabled"
        super().__init__(_msg)


class WorkflowNotFound(Exception):
    def __init__(self, projectid, wfid):
        _msg = f"projectid: {projectid} and wfid: {wfid} not found"
        super().__init__(_msg)


class ProjectNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)


class PrivateKeyNotFound(Exception):
    def __init__(self, projectid):
        super().__init__(f"Private Key not found for project {projectid}")
