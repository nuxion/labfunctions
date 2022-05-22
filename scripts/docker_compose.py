import sys

from labfunctions.conf.jtemplates import render_to_file
from labfunctions.utils import get_version

ip_addr = sys.argv[1]
version = get_version()

data = dict(ip=ip_addr, version=version)

render_to_file("docker-compose.yaml", dst="docker/docker-compose.yaml", data=data)
