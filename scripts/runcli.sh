#!/bin/bash

if [ -f ".env.docker" ]; then
	CMD_PARAMS="--rm -it -e LF_SERVER=yes --env-file=.env.docker nuxion/labfunctions:0.8.0-alpha.8 bash"
else
	CMD_PARAMS="--rm -it -e LF_SERVER=yes nuxion/labfunctions:0.8.0-alpha.8 bash"
fi
echo "Running docker run ${CMD_PARAMS}"
docker run $CMD_PARAMS
