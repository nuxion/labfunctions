class LoginError(Exception):
    def __init__(self, addr, user):
        msg = f"{user} failed auth to server {addr}"
        super().__init__(msg)


class WorkflowStateNotSetError(Exception):
    def __init__(self, module_name):
        msg = f"WorkflowState is not set in {module_name}"
        super().__init__(msg)
