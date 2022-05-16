#!/bin/bash

VERSION="0.8.0-alpha.8"

if [ -f ".env.docker" ]; then
    CMD_PARAMS="--rm -it -e LF_SERVER=yes --network=labfunctions_lab --env-file=.env.docker nuxion/labfunctions:${VERSION} bash"
else
	CMD_PARAMS="--rm -it -e LF_SERVER=yes --network=labfunctions_lab nuxion/labfunctions:${VERSION} bash"
fi
echo "Running docker run ${CMD_PARAMS}"
docker run $CMD_PARAMS
