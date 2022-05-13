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
GIT_TAG := $(shell git describe --tags)
CUDA=11.6
# from poetry pyproject.toml
LF_VERSION :=$(shell python scripts/get_version.py)
FULLPY_PKG := $(shell python scripts/get_package_name.py)
API_VERSION := "v1"
BUILD := $(shell git rev-parse --short HEAD)
PROJECTNAME := $(shell basename "$(PWD)")
PACKAGE_DIR = $(shell basename "$(PWD)")
DOCKERID = $(shell echo "nuxion")
# REGISTRY := registry.nyc1.algorinfo
# RANDOM := $(shell echo $RANDOM | md5sum | head -c 20; echo;)

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
	rm -rf docker/client/dist
	rm -rf docker/all/dist

lock-dev:
	poetry export -f requirements.txt --output requirements/requirements_dev.txt --extras server --without-hashes --dev

lock-all:
	poetry export -f requirements.txt --output requirements/requirements_all.txt --without-hashes --extras server --extras cloud

lock-client:
	poetry export -f requirements.txt --output requirements/requirements_client.txt --without-hashes
	cp requirements/requirements_client.txt labfunctions/conf/templates/requirements_client.txt

lock: lock-all lock-client lock-dev

build: lock
	poetry build
	echo ${PWD}
	tar xvfz dist/${FULLPY_PKG}.tar.gz -C dist/
	cp dist/${FULLPY_PKG}/setup.py .

preversion: 
	poetry version prerelease
	./scripts/update_versions.sh ${API_VERSION}

minor: 
	poetry version minor
	./scripts/update_versions.sh ${API_VERSION}

black:
	black --config ./.black.toml labfunctions tests

isort:
	isort labfunctions tests --profile=black

lint: black isort

.PHONY: test
test:
	PYTHONPATH=$(PWD) pytest --cov-report xml --cov=labfunctions tests/

.PHONY: test-html
test-html:
	PYTHONPATH=$(PWD) pytest --cov-report=html --cov=labfunctions tests/


.PHONY: e2e
e2e:
	pytest -s -k test_ e2e/

.PHONY: install
install:
	poetry install --dev

.PHONY: web
web:
	lab web --apps workflows,history,projects,runtimes -A --workers 1 -L

agent:
	poetry run lab agent run --qnames cpu,gpu,build,control -m local/ba/asd

.PHONY: docker-client
docker-client:
	docker build -t ${DOCKERID}/${PROJECTNAME}:latest-client -f docker/Dockerfile.client .
	docker tag ${DOCKERID}/${PROJECTNAME}:latest-client ${DOCKERID}/${PROJECTNAME}:${LF_VERSION}-client

.PHONY: docker-client-gpu
docker-client-gpu:
	docker build -t ${DOCKERID}/${PROJECTNAME}:latest-client-cuda${CUDA} -f docker/Dockerfile.client.gpu .
	docker tag ${DOCKERID}/${PROJECTNAME}:latest-client-cuda${CUDA} ${DOCKERID}/${PROJECTNAME}:${LF_VERSION}-client-cuda${CUDA}

.PHONY: docker-all
docker-all:
	docker build -t ${DOCKERID}/${PROJECTNAME} -f docker/Dockerfile.all .
	docker tag ${DOCKERID}/${PROJECTNAME}:latest ${DOCKERID}/${PROJECTNAME}:$(LF_VERSION)

.PHONY: docker
docker: docker-client docker-client-gpu docker-all

.PHONY: docker-release
docker-release: docker
	docker push ${DOCKERID}/${PROJECTNAME}:$(LF_VERSION)
	docker push ${DOCKERID}/${PROJECTNAME}:$(LF_VERSION)-client
	docker push ${DOCKERID}/${PROJECTNAME}:$(LF_VERSION)-client-gpu

.PHONY: publish
publish:
	poetry publish

.PHONY: publish-test
publish-test:
	poetry publish --build -r test

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
