# LabFunctions

[![labfunctions](https://github.com/nuxion/labfunctions/actions/workflows/main.yaml/badge.svg)](https://github.com/nuxion/labfunctions/actions/workflows/main.yaml)
[![readthedocs](https://readthedocs.org/projects/labfunctions/badge/?version=latest)](https://labfunctions.readthedocs.io/en/latest/)
[![PyPI - Version](https://img.shields.io/pypi/v/labfunctions)](https://pypi.org/project/labfunctions/)
[![PyPI - Format](https://img.shields.io/pypi/format/labfunctions)](https://pypi.org/project/labfunctions/)
[![PyPI - Status](https://img.shields.io/pypi/status/labfunctions)](https://pypi.org/project/labfunctions/)
[![Docker last](https://img.shields.io/docker/v/nuxion/labfunctions/0.7.0)](https://hub.docker.com/r/nuxion/labfunctions/tags)
[![codecov](https://codecov.io/gh/nuxion/labfunctions/branch/main/graph/badge.svg?token=F025Y1BF9U)](https://codecov.io/gh/nuxion/labfunctions)


## Description 

LabFunctions is a library and a service that allows you to run parametrized notebooks on demand.

It was thought to empower different data roles to put notebooks into production whatever they do, this notebooks could be models, ETL process, crawlers, etc. This way of working should allow going backward and foreward in the process of building data products. 

Although this tool allow different workflows in a data project, we propose this one as an example:
![Workflow](./docs/img/schemas-workflow.jpg)

## Philosophy

LabFunctions isn't a complete MLOps solution. 

We try hard to expose the right APIs to the user for the part of scheduling notebooks with reproducibility in mind.

Whenever possible we try to use well established open source tools, projects and libraries to resolve common problems. Moreover we force some good practices like code versioning, and the use of containers to run wokrloads 


The idea comes from a [Netflix post](https://netflixtechblog.com/notebook-innovation-591ee3221233) which suggest using notebooks like an interface or a some kind of DSL to orchestrate different workloads like Spark and so on. But it also could be used to run entire process as we said before.

The benefits of this approach is that notebooks runned could be stored and inspected for good or for bad executions. If something fails, is easy to run in a classical way: cell by cell in a local pc or in a remote server. 

## Status

> ⚠️ Although the project is considered stable 
> please keep in mind that LabFunctions is still under active development
> and therefore full backward compatibility is not guaranteed before reaching v1.0.0., APIS could change.


## Features

Some features can be used standalone, and others depend on each other.

| Feature             | Status |  Note   |
| --------------------| ------ | ------- |
| Notebook execution  | Stable |  - |
| Workflow scheduling | Beta   | This allow to schedule: every hour, every day, etc |
| Build Runtimes      | Beta   | Build OCI compliance continers (Docker) and store it. | 
| Runtimes templates  | Stable | Genereate Dockerfile based on templates
| Create and destroy servers | Alpha | Create and delete Machines in different cloud providers |
| GPU Support | Beta | Allows to run workloads that requires GPU 
| Execution History | Alpha | Track notebooks & workflows executions |
| Google Cloud support | Beta | Support google store and google cloud as provider |
| Secrets managment | Alpha | Encrypt and manager private data in a project | 
| Project Managment | Alpha | Match each git repostiroy to a project |


## Cluster options

It is possible to run different cluster configurations with custom auto scalling policies

![GPU CLUSTER DEMO](https://media.giphy.com/media/OnhmnYiCJpe2FsTmaP/giphy.gif)

Instances inside a cluster could be created manually or automatically

See a simple demo of a gpu cluster creation

[https://www.youtube.com/watch?v=-R7lJ4dGI9s](https://www.youtube.com/watch?v=-R7lJ4dGI9s)


## :earth_americas: Roadmap

See [Roadmap](/ROADMAP.md) *draft*

## :post_office: Architecture

![labfunctions architecture](/docs/img/platform-workflows.jpg)


## :bookmark_tabs: References & inspirations
- [Notebook Innovation - Netflix](https://netflixtechblog.com/notebook-innovation-591ee3221233)
- [Tensorflow metastore](https://www.tensorflow.org/tfx/guide/mlmd)
- [Maintainable and collaborative pipelines](https://blog.jupyter.org/ploomber-maintainable-and-collaborative-pipelines-in-jupyter-acb3ad2101a7)
- [The magic of Merlin](https://shopify.engineering/merlin-shopify-machine-learning-platform)
- [Scale aware approach](https://queue.acm.org/detail.cfm?id=3025012)


## Contributing

Bug reports and pull requests are welcome on GitHub at the [issues
page](https://github.com/nuxion/labfunctions). This project is intended to be
a safe, welcoming space for collaboration, and contributors are expected to
adhere to the [Contributor Covenant](http://contributor-covenant.org) code of
conduct.


## License

This project is licensed under Apache 2.0. Refer to
[LICENSE.txt](https://github.com/nuxion/labfunctions/blob/main/LICENSE).
