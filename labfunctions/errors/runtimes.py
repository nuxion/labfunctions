class RuntimeCreationError(Exception):
    def __init__(self, docker_name, projectid):
        msg = f"Error with the creation of runtime {docker_name} for {projectid}"
        super().__init__(msg)


class RuntimeNotFound(Exception):
    def __init__(self, runtimeid):
        _msg = f"runtimeid: {runtimeid} not found"
        super().__init__(_msg)
