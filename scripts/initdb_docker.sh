#!/bin/bash
echo "Creating db"
docker run --rm -it --network=nb_workflows_nb \
	-e NB_SQL=postgresql://nb_workflows:secret@postgres:5432/nb_workflows \
	-e NB_SERVER=true nuxion/nb_workflows nb manager db create

echo "Now a user should be created"
docker run --rm -it --network=nb_workflows_nb \
	-e NB_SQL=postgresql://nb_workflows:secret@postgres:5432/nb_workflows \
	-e NB_SERVER=true nuxion/nb_workflows nb manager users create


