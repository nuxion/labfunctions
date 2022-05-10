#!/bin/sh
set -e
API_VERSION=${1:-v1}
PKG_VERSION=`python scripts/get_version.py`
PKG_NAME=labfunctions


cat <<EOT > ${PKG_NAME}/__version__.py
__version__ = "${PKG_VERSION}"
__api_version__ = "${API_VERSION}"
EOT
