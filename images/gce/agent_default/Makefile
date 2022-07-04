.EXPORT_ALL_VARIABLES:
# VERSION := $(shell git describe --tags)
# BUILD := $(shell git rev-parse --short HEAD)
# PROJECTNAME := $(shell basename "$(PWD)")
PROJECTNAME := nyc1

# LDFLAGS=-ldflags "-X=main.Version=$(VERSION) -X=main.Build=$(BUILD)"
# STDERR := /tmp/.$(PROJECTNAME)-stderr.txt
#
.PHONY: init
init:
	packer init .

.PHONY: validate
validate:
	packer validate .

.PHONY: build
build: validate
	packer build .
