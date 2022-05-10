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
tarfile := labfunctions-${VERSION}.tar.gz
filename := labfunctions-${VERSION}

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

black:
	black --config ./.black.toml labfunctions tests

isort:
	isort labfunctions tests --profile=black

lint: black isort

.PHONY: test
test:
	PYTHONPATH=$(PWD) pytest tests/

.PHONY: docker
docker:
	docker build -t ${DOCKERID}/${PROJECTNAME} -f Dockerfile.nbruntime .

.PHONY: docker-local
docker-local:
	docker build -t ${DOCKERID}/${PROJECTNAME} -f Dockerfile.nbruntime .
	docker tag ${DOCKERID}/${PROJECTNAME} ${DOCKERID}/${PROJECTNAME}:$(VERSION)

.PHONY: release
release:
	docker tag ${DOCKERID}/${PROJECTNAME} ${REGISTRY}/${DOCKERID}/${PROJECTNAME}:$(VERSION)
	docker push ${REGISTRY}/${DOCKERID}/${PROJECTNAME}:$(VERSION)

