#!/bin/bash
NEXT_ID=`ls labfunctions/migrations/versions/* | grep -P '/\d{4}_.*\.py$' | wc -l`
	alembic -c labfunctions/alembic.ini revision --autogenerate -m $@ --rev-id=`printf "%04d" ${NEXT_ID}`


