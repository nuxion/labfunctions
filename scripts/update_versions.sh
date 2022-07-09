#!/bin/sh
set -e
API_VERSION=${1:-v1}
POETRY_VERSION=`python scripts/get_version.py`
PKG_NAME=labfunctions

PKG_VERSION=`python scripts/get_package_version.py`
PACKER_VERSION=`python scripts/get_packer_version.py`

cat <<EOT > ${PKG_NAME}/__version__.py
__version__ = "${POETRY_VERSION}"
__api_version__ = "${API_VERSION}"
EOT

# runtimes
sed -i "s/pkg_version:.*/pkg_version: ${PKG_VERSION}/g" runtimes.yaml
sed -i "s/VERSION=.*/VERSION=${POETRY_VERSION}/g" scripts/runcli.sh

# packer images
sed -i "s/DOCKER_VERSION:=.*/DOCKER_VERSION:=${POETRY_VERSION}/g" images/gce/agent_default/Makefile
sed -i "s/IMG_VERSION:=.*/IMG_VERSION:=${PACKER_VERSION}/g" images/gce/agent_default/Makefile

sed -i "s/DOCKER_VERSION:=.*/DOCKER_VERSION:=${POETRY_VERSION}/g" images/gce/agent_nvidia/Makefile
sed -i "s/IMG_VERSION:=.*/IMG_VERSION:=${PACKER_VERSION}/g" images/gce/agent_nvidia/Makefile


# cluster.example.yaml
sed -i "s/image: lab-agent-.*/image: lab-agent-${PACKER_VERSION}/g" cluster.example.yaml
sed -i "s/image: lab-nvidia-.*/image: lab-nvidia-${PACKER_VERSION}/g" cluster.example.yaml





