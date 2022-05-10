class ClusterSpecNotFound(Exception):
    def __init__(self, cluster, yaml_file):
        _msg = f"cluster {cluster} not found in file {yaml_file}"
        super().__init__(_msg)
