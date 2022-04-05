class RuntimeCreationError(Exception):
    def __init__(self, docker_name, projectid):
        msg = f"Error with the creation of runtime {docker_name} for {projectid}"
        super().__init__(msg)
