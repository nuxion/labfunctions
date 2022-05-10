class LoginError(Exception):
    def __init__(self, addr, user):
        msg = f"{user} failed auth to server {addr}"
        super().__init__(msg)


class WorkflowStateNotSetError(Exception):
    def __init__(self, module_name):
        msg = f"WorkflowState is not set in {module_name}"
        super().__init__(msg)


class ProjectUploadError(Exception):
    def __init__(self, projectid):
        msg = f"Upload Failed from project {projectid}"
        super().__init__(msg)


class ProjectCreateError(Exception):
    def __init__(self, projectid):
        msg = f"Project creation error for projectid or name: {projectid}"
        super().__init__(msg)
