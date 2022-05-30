# LabFunctions

[![labfunctions](https://github.com/nuxion/labfunctions/actions/workflows/main.yaml/badge.svg)](https://github.com/nuxion/labfunctions/actions/workflows/main.yaml)
[![readthedocs](https://readthedocs.org/projects/labfunctions/badge/?version=latest)](https://labfunctions.readthedocs.io/en/latest/)
[![PyPI - Version](https://img.shields.io/pypi/v/labfunctions)](https://pypi.org/project/labfunctions/)
[![PyPI - Format](https://img.shields.io/pypi/format/labfunctions)](https://pypi.org/project/labfunctions/)
[![PyPI - Status](https://img.shields.io/pypi/status/labfunctions)](https://pypi.org/project/labfunctions/)
[![Docker last](https://img.shields.io/docker/v/nuxion/labfunctions/0.7.0)](https://hub.docker.com/r/nuxion/labfunctions/tags)
[![codecov](https://codecov.io/gh/nuxion/labfunctions/branch/main/graph/badge.svg?token=F025Y1BF9U)](https://codecov.io/gh/nuxion/labfunctions)


## :books: Description 

LabFunctions empowers different data roles to put notebooks into production, simplifying the time required to do so. It enables people to go from a data exploration instance to an entirely project deployed in production, using the same notebooks files made by a data scientist, analyst or whatever role working with data in an iterative way.

LabFunctions is a library and a service that allows you to run parametrized notebooks in a distributed way.  

A Notebook could be launched remotly on demand, or could be scheduled by intervals or using cron syntax.

Internally it uses [Sanic](https://sanicframework.org) as web server, [papermill](https://papermill.readthedocs.io/en/latest/) as notebook executor, an [RQ](https://python-rq.org/)
for task distributions and coordination. 

:tada: Demo :tada: 

:floppy_disk: [Example project](
https://github.com/nuxion/nbwf-demo2)


## :telescope: Philosophy

LabFunctions it insn't a complete MLOps solution.

We try hard to simply and expose the right APIs to the user for the part of scheduling notebooks with reproducibility in mind.

We also try to give the user the same freedom that lego tiles can gives, but we are opinated in the sense that all code, artifact, dependency and environment should be declareted

With this point of view, then: 

1) Git is neccesary :wink:
2) Docker is necessary for environment reproducibility. 
3) Although you can push not versioned code,  versioning is almost enforced, and is always a good practice in software development

The idea comes from a [Netflix post](https://netflixtechblog.com/notebook-innovation-591ee3221233) which suggest using notebooks like an interface or a some kind of DSL to orchestrate different workloads like Spark and so on. But it also could be used to run entire process: like training a model, crawlings sites, performing etls, and so on. 

The benefits of this approach is that notebooks runned could be stored and inspected for good or for bad. If something fails, is easy to run in a classical way: cell by cell. 

The last point to clarify and it could challange the common sense or the way that we are used to use Jupyter's Notebooks, is that each notebook is more like a function definition with inputs and outputs, so a notebook potentially could be used for different purposes, hence the name of **workflow**, and indeed this idea is common in the data space. Then a workflow will be a notebook with params defined to be used anytime that a user wants, altering or not the parameters sent. 


## :nut_and_bolt: Features

- Define a notebook like a function, and execute it on demand or scheduling it
- Automatic Dockerfile generation. A project should share a unique environment but could use different versions of the same environment
- Execution History, Notifications to Slack or Discord.
- Cluster creation applying scaling policies by idle time or/and enqueued items

## Cluster options

It is possible to run different cluster configurations with custom auto scalling policies

![GPU CLUSTER DEMO](https://media.giphy.com/media/OnhmnYiCJpe2FsTmaP/giphy.gif)

Instances inside a cluster could be created manually or automatically

See a simple demo of a gpu cluster creation

[https://www.youtube.com/watch?v=-R7lJ4dGI9s](https://www.youtube.com/watch?v=-R7lJ4dGI9s)


## Installation

### Server

### Docker-compose

The project provides a [docker-compose.yaml](./docker-compose.yaml) file as en example. 

:construction: Note :construction:

Because **NB Workflows** will spawn docker instance for each workload, the installation inside docker containers could be tricky. 
The most difficult part is the configuration of the worker that needs access to the [docker socket](https://docs.docker.com/engine/reference/commandline/dockerd/#daemon-socket-option).

A [Dockerfile](./Dockerfile) is provided for customization of uid and guid witch should match with the local environment. A second alternative is expose the docker daemon through HTTP, if that is the case a `DOCKER_HOST` env could be used, see [docker client sdk](https://docker-py.readthedocs.io/en/stable/client.html)


```
git clone https://github.com/nuxion/labfunctions
cd labfunctions
```

The next step is intializing the database and creating a user (*please review the script first*):

```
docker-compose postgres up -d 
./scripts/initdb_docker.sh
```
Now you can start everything else:
```
docker-compose up -d 
```

### Without docker

```
pip install nb-workflows[server]==0.6.0
```

first terminal:

```
export NB_SERVER=True
nb manager db upgrade
nb manager users create
nb web --apps workflows,history,projects,events,runtimes
```

second terminal:

```
nb rqworker -w 1 -q control,mch.default
```

Before all that, redis postgresql and the [nginx in webdav mode](./fileserver.conf) should be configurated

### Client

Client: 

```
pip install nb-workflows==0.6.0
nb startporject .
```


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
