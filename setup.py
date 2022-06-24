# -*- coding: utf-8 -*-
from setuptools import setup

packages = [
    "labfunctions",
    "labfunctions.client",
    "labfunctions.cluster",
    "labfunctions.cluster.providers",
    "labfunctions.cmd",
    "labfunctions.conf",
    "labfunctions.conf.templates",
    "labfunctions.control",
    "labfunctions.control_plane",
    "labfunctions.db",
    "labfunctions.errors",
    "labfunctions.executors",
    "labfunctions.io",
    "labfunctions.managers",
    "labfunctions.migrations",
    "labfunctions.migrations.versions",
    "labfunctions.notebooks",
    "labfunctions.runtimes",
    "labfunctions.security",
    "labfunctions.types",
    "labfunctions.web",
]

package_data = {"": ["*"]}

install_requires = [
    "Jinja2>=3.0.3,<4.0.0",
    "PyJWT>=2.1.0,<2.2.0",
    "PyYAML>=6.0,<7.0",
    "aiofiles>=0.8.0,<0.9.0",
    "aiosqlite>=0.17.0,<0.18.0",
    "asyncssh>=2.10.0,<3.0.0",
    "click>=8.0.1,<9.0.0",
    "cloudpickle>=2.0.0,<3.0.0",
    "cryptography>=36.0.1,<37.0.0",
    "dateparser>=1.1.0,<2.0.0",
    "docker>=5.0.3,<6.0.0",
    "hiredis>=2.0.0,<3.0.0",
    "httpx<0.22.0",
    "ipykernel>=6.9.1,<7.0.0",
    "jupytext>=1.13.0,<2.0.0",
    "libq>=0.7.2,<0.8.0",
    "loky>=3.0.0,<4.0.0",
    "nanoid>=2.0.0,<3.0.0",
    "nbconvert>=6.2.0,<7.0.0",
    "papermill>=2.3.4,<3.0.0",
    "pydantic>=1.9.0,<2.0.0",
    "pytz>=2022.1,<2023.0",
    "redis>=4.3.1,<5.0.0",
    "rich>=12.0.0,<13.0.0",
    "tenacity>=8.0.1,<9.0.0",
    "tqdm>=4.62.3,<5.0.0",
]

extras_require = {
    "cloud": ["apache-libcloud>=3.5.1,<4.0.0"],
    "server": [
        "uvloop>=0.16.0,<0.17.0",
        "sanic>=21.6.2,<22.0.0",
        "sanic-openapi>=21.6.1,<22.0.0",
        "sanic-ext>=21.9.0,<22.0.0",
        "SQLAlchemy[asyncio]>=1.4.26,<2.0.0",
        "SQLAlchemy-serializer>=1.4.1,<2.0.0",
        "psycopg2-binary>=2.9.1,<3.0.0",
        "asyncpg>=0.24.0,<0.25.0",
        "alembic>=1.6.5,<2.0.0",
    ],
    "stores": ["smart-open[gcs,s3]>=6.0.0,<7.0.0"],
}

entry_points = {"console_scripts": ["lab = labfunctions.cli:cli"]}

setup_kwargs = {
    "name": "labfunctions",
    "version": "0.9.0a5",
    "description": "Schedule parameterized notebooks programmatically using cli or a REST API",
    "long_description": "# LabFunctions\n\n[![labfunctions](https://github.com/nuxion/labfunctions/actions/workflows/main.yaml/badge.svg)](https://github.com/nuxion/labfunctions/actions/workflows/main.yaml)\n[![readthedocs](https://readthedocs.org/projects/labfunctions/badge/?version=latest)](https://labfunctions.readthedocs.io/en/latest/)\n[![PyPI - Version](https://img.shields.io/pypi/v/labfunctions)](https://pypi.org/project/labfunctions/)\n[![PyPI - Format](https://img.shields.io/pypi/format/labfunctions)](https://pypi.org/project/labfunctions/)\n[![PyPI - Status](https://img.shields.io/pypi/status/labfunctions)](https://pypi.org/project/labfunctions/)\n[![Docker last](https://img.shields.io/docker/v/nuxion/labfunctions/0.7.0)](https://hub.docker.com/r/nuxion/labfunctions/tags)\n[![codecov](https://codecov.io/gh/nuxion/labfunctions/branch/main/graph/badge.svg?token=F025Y1BF9U)](https://codecov.io/gh/nuxion/labfunctions)\n\n\n## :books: Description \n\nLabFunctions empowers different data roles to put notebooks into production, simplifying the time required to do so. It enables people to go from a data exploration instance to an entirely project deployed in production, using the same notebooks files made by a data scientist, analyst or whatever role working with data in an iterative way.\n\nLabFunctions is a library and a service that allows you to run parametrized notebooks in a distributed way.  \n\nA Notebook could be launched remotly on demand, or could be scheduled by intervals or using cron syntax.\n\nInternally it uses [Sanic](https://sanicframework.org) as web server, [papermill](https://papermill.readthedocs.io/en/latest/) as notebook executor, an [RQ](https://python-rq.org/)\nfor task distributions and coordination. \n\n:tada: Demo :tada: \n\n:floppy_disk: [Example project](\nhttps://github.com/nuxion/nbwf-demo2)\n\n\n## :telescope: Philosophy\n\nLabFunctions it insn't a complete MLOps solution.\n\nWe try hard to simply and expose the right APIs to the user for the part of scheduling notebooks with reproducibility in mind.\n\nWe also try to give the user the same freedom that lego tiles can gives, but we are opinated in the sense that all code, artifact, dependency and environment should be declareted\n\nWith this point of view, then: \n\n1) Git is neccesary :wink:\n2) Docker is necessary for environment reproducibility. \n3) Although you can push not versioned code,  versioning is almost enforced, and is always a good practice in software development\n\nThe idea comes from a [Netflix post](https://netflixtechblog.com/notebook-innovation-591ee3221233) which suggest using notebooks like an interface or a some kind of DSL to orchestrate different workloads like Spark and so on. But it also could be used to run entire process: like training a model, crawlings sites, performing etls, and so on. \n\nThe benefits of this approach is that notebooks runned could be stored and inspected for good or for bad. If something fails, is easy to run in a classical way: cell by cell. \n\nThe last point to clarify and it could challange the common sense or the way that we are used to use Jupyter's Notebooks, is that each notebook is more like a function definition with inputs and outputs, so a notebook potentially could be used for different purposes, hence the name of **workflow**, and indeed this idea is common in the data space. Then a workflow will be a notebook with params defined to be used anytime that a user wants, altering or not the parameters sent. \n\n\n## :nut_and_bolt: Features\n\n- Define a notebook like a function, and execute it on demand or scheduling it\n- Automatic Dockerfile generation. A project should share a unique environment but could use different versions of the same environment\n- Execution History, Notifications to Slack or Discord.\n- Cluster creation applying scaling policies by idle time or/and enqueued items\n\n## Cluster options\n\nIt is possible to run different cluster configurations with custom auto scalling policies\n\n![GPU CLUSTER DEMO](https://media.giphy.com/media/OnhmnYiCJpe2FsTmaP/giphy.gif)\n\nInstances inside a cluster could be created manually or automatically\n\nSee a simple demo of a gpu cluster creation\n\n[https://www.youtube.com/watch?v=-R7lJ4dGI9s](https://www.youtube.com/watch?v=-R7lJ4dGI9s)\n\n\n## Installation\n\n### Server\n\n### Docker-compose\n\nThe project provides a [docker-compose.yaml](./docker-compose.yaml) file as en example. \n\n:construction: Note :construction:\n\nBecause **NB Workflows** will spawn docker instance for each workload, the installation inside docker containers could be tricky. \nThe most difficult part is the configuration of the worker that needs access to the [docker socket](https://docs.docker.com/engine/reference/commandline/dockerd/#daemon-socket-option).\n\nA [Dockerfile](./Dockerfile) is provided for customization of uid and guid witch should match with the local environment. A second alternative is expose the docker daemon through HTTP, if that is the case a `DOCKER_HOST` env could be used, see [docker client sdk](https://docker-py.readthedocs.io/en/stable/client.html)\n\n\n```\ngit clone https://github.com/nuxion/labfunctions\ncd labfunctions\n```\n\nThe next step is intializing the database and creating a user (*please review the script first*):\n\n```\ndocker-compose postgres up -d \n./scripts/initdb_docker.sh\n```\nNow you can start everything else:\n```\ndocker-compose up -d \n```\n\n### Without docker\n\n```\npip install nb-workflows[server]==0.6.0\n```\n\nfirst terminal:\n\n```\nexport NB_SERVER=True\nnb manager db upgrade\nnb manager users create\nnb web --apps workflows,history,projects,events,runtimes\n```\n\nsecond terminal:\n\n```\nnb rqworker -w 1 -q control,mch.default\n```\n\nBefore all that, redis postgresql and the [nginx in webdav mode](./fileserver.conf) should be configurated\n\n### Client\n\nClient: \n\n```\npip install nb-workflows==0.6.0\nnb startporject .\n```\n\n\n## :earth_americas: Roadmap\n\nSee [Roadmap](/ROADMAP.md) *draft*\n\n## :post_office: Architecture\n\n![labfunctions architecture](/docs/img/platform-workflows.jpg)\n\n\n## :bookmark_tabs: References & inspirations\n- [Notebook Innovation - Netflix](https://netflixtechblog.com/notebook-innovation-591ee3221233)\n- [Tensorflow metastore](https://www.tensorflow.org/tfx/guide/mlmd)\n- [Maintainable and collaborative pipelines](https://blog.jupyter.org/ploomber-maintainable-and-collaborative-pipelines-in-jupyter-acb3ad2101a7)\n- [The magic of Merlin](https://shopify.engineering/merlin-shopify-machine-learning-platform)\n- [Scale aware approach](https://queue.acm.org/detail.cfm?id=3025012)\n\n\n## Contributing\n\nBug reports and pull requests are welcome on GitHub at the [issues\npage](https://github.com/nuxion/labfunctions). This project is intended to be\na safe, welcoming space for collaboration, and contributors are expected to\nadhere to the [Contributor Covenant](http://contributor-covenant.org) code of\nconduct.\n\n\n## License\n\nThis project is licensed under Apache 2.0. Refer to\n[LICENSE.txt](https://github.com/nuxion/labfunctions/blob/main/LICENSE).\n",
    "author": "nuxion",
    "author_email": "nuxion@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/nuxion/labfunctions",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "extras_require": extras_require,
    "entry_points": entry_points,
    "python_requires": ">=3.7,<3.11",
}


setup(**setup_kwargs)
