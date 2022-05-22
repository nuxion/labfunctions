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


class WorkflowRegisterError(Exception):
    def __init__(self, project, alias, e):
        if "_nb_workflow__project_alias" in str(e):
            _msg = f"Alias {alias} for {project} already exist"
        else:
            _msg = f"Error registering {alias} for project {project}"
        super().__init__(_msg)


class WorkflowRegisterClientError(Exception):
    def __init__(self, project, wfid):
        _msg = f"Registration error for workflow {wfid} in {project}"
        super().__init__(_msg)


class HistoryNotebookError(Exception):
    def __init__(self, addr, uri):
        _msg = f"Error getting {uri} from {addr}"
        super().__init__(_msg)


class ProjectNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)


class PrivateKeyNotFound(Exception):
    def __init__(self, projectid):
        super().__init__(f"Private Key not found for project {projectid}")


class AuthValidationFailed(Exception):
    pass
