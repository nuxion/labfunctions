#!/bin/sh
set -e
API_VERSION=${1:-v1}
POETRY_VERSION=`python scripts/get_version.py`
PKG_NAME=labfunctions

PKG_VERSION=`python scripts/get_package_version.py`

cat <<EOT > ${PKG_NAME}/__version__.py
__version__ = "${POETRY_VERSION}"
__api_version__ = "${API_VERSION}"
EOT

sed -i "s/pkg_version:.*/pkg_version: ${PKG_VERSION}/g" runtimes.yaml
sed -i "s/VERSION=.*/VERSION=${POETRY_VERSION}/g" scripts/runcli.sh
