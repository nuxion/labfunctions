define USAGE
Super awesome hand-crafted build system ⚙️

Commands:
	setup     Install dependencies, dev included
	lock      Generate requirements.txt
	test      Run tests
	lint      Run linting tests
	run       Run docker image with --rm flag but mounted dirs.
	release   Publish docker image based on some variables
	docker    Build the docker image
	tag    	  Make a git tab using poetry information

endef

export USAGE
.EXPORT_ALL_VARIABLES:
VERSION := $(shell git describe --tags)
BUILD := $(shell git rev-parse --short HEAD)
PROJECTNAME := $(shell basename "$(PWD)")
PACKAGE_DIR = $(shell basename "$(PWD)")
DOCKERID = $(shell echo "nuxion")
REGISTRY := registry.nyc1.algorinfo
tarfile := nb_workflows-${VERSION}.tar.gz
filename := nb_workflows-${VERSION}

help:
	@echo "$$USAGE"

.PHONY: startenv
startenv:
	poetry shell
	docker-compose start 
	alembic upgrade head


clean:
	find . ! -path "./.eggs/*" -name "*.pyc" -exec rm {} \;
	find . ! -path "./.eggs/*" -name "*.pyo" -exec rm {} \;
	find . ! -path "./.eggs/*" -name ".coverage" -exec rm {} \;
	rm -rf build/* > /dev/null 2>&1
	rm -rf dist/* > /dev/null 2>&1
	rm -rf .ipynb_checkpoints/* > /dev/null 2>&1

lock-dev:
	poetry export -f requirements.txt --output requirements/requirements_dev.txt --extras server --without-hashes --dev

lock-server:
	poetry export -f requirements.txt --output requirements/requirements.txt --without-hashes --extras server

lock-client:
	poetry export -f requirements.txt --output requirements/requirements_client.txt --without-hashes

lock: lock-server lock-client lock-dev

prepare: lock
	poetry build
	echo ${PWD}
	tar xvfz dist/${tarfile} -C dist/
	cp dist/${filename}/setup.py .
	rm -Rf dist/

black:
	black --config ./.black.toml nb_workflows tests

isort:
	isort nb_workflows tests --profile=black

lint: black isort

.PHONY: test
test:
	PYTHONPATH=$(PWD) pytest --cov=nb_workflows tests/

.PHONY: test-html
test-html:
	PYTHONPATH=$(PWD) pytest --cov-report=html --cov=nb_workflows tests/

.PHONY: install
install:
	poetry install --dev

.PHONY: run
run:
	docker run --rm -p 127.0.0.1:8100:8000 -p 127.0.0.1:8110:8001 ${DOCKERID}/${PROJECTNAME}

.PHONY: web
web:
	poetry run nb web --apps workflows,history,projects --workers 1 -L

.PHONY: rqworker
rqworker:
	poetry run nb rqworker -w 1

.PHONY: rqscheduler
rqscheduler:
	poetry run nb rqscheduler

.PHONY: jupyter
jupyter:
	poetry run jupyter lab --NotebookApp.token=testing

.PHONY: docker
docker:
	docker build -t ${DOCKERID}/${PROJECTNAME} .

.PHONY: docker-local
docker-local:
	docker build -t ${DOCKERID}/${PROJECTNAME} .
	docker tag ${DOCKERID}/${PROJECTNAME} ${DOCKERID}/${PROJECTNAME}:$(VERSION)

.PHONY: release
release:
	docker tag ${DOCKERID}/${PROJECTNAME} ${REGISTRY}/${DOCKERID}/${PROJECTNAME}:$(VERSION)
	docker push ${REGISTRY}/${DOCKERID}/${PROJECTNAME}:$(VERSION)

.PHONY: publish
publish:
	poetry publish --build

.PHONY: publish-test
publish-test:
	poetry publish --build -r test

.PHONY: docker-env
docker-env:
	# docker run --rm -it --network host --env-file=.env.docker -v ${PWD}:/app ${REGISTRY}/${DOCKERID}/${PROJECTNAME}:${VERSION} bash
	docker run --rm -it --network host --env-file=.env.docker  -v /tmp/plasma:/tmp/plasma -v ${PWD}:/app ${DOCKERID}/${PROJECTNAME} bash
.PHONY: redis-cli
redis-cli:
	docker-compose exec redis redis-cli

.PHONY: docs-server
docs-serve:
	sphinx-autobuild docs docs/_build/html --port 9292 --watch ./

.PHONY: tag
tag:
	# https://git-scm.com/docs/pretty-formats/2.20.0
	#poetry version prealese
	git tag -a $(shell poetry version --short) -m "$(shell git log -1 --pretty=%s | head -n 1)"
