#!/bin/bash
NEXT_ID=`ls nb_workflows/db/migrations/versions/* | grep -P '/\d{4}_.*\.py$' | wc -l`
	alembic -c nb_workflows/db/alembic.ini revision --autogenerate -m $@ --rev-id=`printf "%04d" ${NEXT_ID}`


