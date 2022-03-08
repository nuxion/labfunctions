# NB Workflows

[![nb-workflows](https://github.com/nuxion/nb_workflows/actions/workflows/main.yaml/badge.svg)](https://github.com/nuxion/nb_workflows/actions/workflows/main.yaml)
![readthedocs](https://readthedocs.org/projects/nb_workflows/badge/?version=latest)
![PyPI - Format](https://img.shields.io/pypi/format/nb_workflows)
![PyPI - Status](https://img.shields.io/pypi/status/nb_workflows)

[![codecov](https://codecov.io/gh/nuxion/nb_workflows/branch/main/graph/badge.svg?token=F025Y1BF9U)](https://codecov.io/gh/nuxion/nb_workflows)


## Description 

If SQL is a lingua franca for querying data, Jupyter should be a lingua franca for data explorations, model training, and complex and unique tasks related to data.

NB Workflows is a library and a platform that allows you to run parameterized notebooks in a distributed way. 
A Notebook could be launched remotly on demand, or could be schedule by intervals or using cron syntax.

Internally it uses [Sanic](https://sanicframework.org) as web server, [papermill](https://papermill.readthedocs.io/en/latest/) as notebook executor, an [RQ](https://python-rq.org/)
for task distributions and coordination. 

### Goal

Empowering different data roles in a project to put code into production, simplifying the time required to do so. It enables people to go from a data exploration instance to an entirely pipeline deployed in production, using the same notebook file made by a data scientist, analyst or whatever role working with data in an iterative way.

### Features

- Define a notebook like a function, and execute it on demand
- Automatic Dockerfile generation. A project should share a unique environment
- Docker building and versioning: it build and track each release. 
- Execution History, Notifications to Slack or Discord.

## Architecture

![nb_workflows architecture](/docs/platform-workflows.jpg)

## References & inspirations
- [Notebook Innovation - Netflix](https://netflixtechblog.com/notebook-innovation-591ee3221233)
- [Tensorflow metastore](https://www.tensorflow.org/tfx/guide/mlmd)
- [Maintainable and collaborative pipelines](https://blog.jupyter.org/ploomber-maintainable-and-collaborative-pipelines-in-jupyter-acb3ad2101a7)

### Alembic configuration
- [version table per package](https://gist.github.com/miohtama/9088958fef0d37e5cb10)
- [Alembic config inside of a package](https://github.com/openstack/neutron/blob/master/neutron/db/migration/alembic.ini)
- [Distributing alembic files](https://stackoverflow.com/questions/42383400/python-packaging-alembic-migrations-with-setuptools)
- [Command API](https://stackoverflow.com/questions/24622170/using-alembic-api-from-inside-application-code/35211383#35211383)

