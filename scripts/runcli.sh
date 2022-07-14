#!/bin/bash

VERSION=0.9.0-alpha.15

if [ -f ".env.docker" ]; then
    CMD_PARAMS="--rm -it -e LF_SERVER=yes \
	    --network=labfunctions_lab \
	    --volume labfunctions_labsecrets:/secrets \
	    --volume labfunctions_labstore:/labstore \
	    --volume ${PWD}/cluster.example.yaml:/app/cluster.example.yaml \
	    --volume ${PWD}/.ssh/:/app/ssh \
	    --volume /var/run/docker.sock:/var/run/docker.sock \
	    --user 1089:991 \
	    --env-file=.env.docker \
	    nuxion/labfunctions:${VERSION} bash"
else
	CMD_PARAMS="--rm -it -e LF_SERVER=yes \
		--network=labfunctions_lab \
		--volume labfunctions_labsecrets:/secrets \
		--volume labfunctions_labstore:/labstore \
	    	--volume /var/run/docker.sock:/var/run/docker.sock \
	    	--volume ${PWD}/cluster.example.yaml:/app/cluster.example.yaml \
	    	--user 1089:991 \
		nauxion/labfunctions:${VERSION} bash"
fi
echo "Running docker run ${CMD_PARAMS}"
docker run $CMD_PARAMS
