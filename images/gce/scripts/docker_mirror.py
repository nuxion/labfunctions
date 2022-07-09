import json
import sys

finalpath = "/etc/docker/daemon.json"
# finalpath = "daemon.json"

try:
    mirror = sys.argv[1]
except IndexError:
    print("Any mirror shared")
    sys.exit(0)

try:
    registry = sys.argv[2]
except IndexError:
    registry = None

daemon = None
if mirror:
    daemon = {"registry-mirrors": [mirror]}

    print("Configuring mirror as ", mirror)
elif registry:
    daemon.update({"insecure-registries": registry})
    print("Configuring  insecure registry ", registry)

if daemon:
    with open(finalpath, "w") as f:
        f.write(json.dumps(daemon))
