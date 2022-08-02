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
    "libq>=0.7.4,<0.8.0",
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
    "version": "0.10.0a0",
    "description": "Schedule parameterized notebooks programmatically using cli or a REST API",
    "long_description": "# LabFunctions\n\n[![labfunctions](https://github.com/labfunctions/labfunctions/actions/workflows/main.yaml/badge.svg)](https://github.com/labfunctions/labfunctions/actions/workflows/main.yaml)\n[![readthedocs](https://readthedocs.org/projects/labfunctions/badge/?version=latest)](https://labfunctions.readthedocs.io/en/latest/)\n[![PyPI - Version](https://img.shields.io/pypi/v/labfunctions)](https://pypi.org/project/labfunctions/)\n[![PyPI - Format](https://img.shields.io/pypi/format/labfunctions)](https://pypi.org/project/labfunctions/)\n[![PyPI - Status](https://img.shields.io/pypi/status/labfunctions)](https://pypi.org/project/labfunctions/)\n[![Docker last](https://img.shields.io/docker/v/labfunctions/labfunctions/0.7.0)](https://hub.docker.com/r/labfunctions/labfunctions/tags)\n[![codecov](https://codecov.io/gh/labfunctions/labfunctions/branch/main/graph/badge.svg?token=F025Y1BF9U)](https://codecov.io/gh/labfunctions/labfunctions)\n\n\n## Description \n\nLabFunctions is a library and a service that allows you to run parametrized notebooks on demand.\n\nIt was thought to empower different data roles to put notebooks into production whatever they do, this notebooks could be models, ETL process, crawlers, etc. This way of working should allow going backward and foreward in the process of building data products. \n\nAlthough this tool allow different workflows in a data project, we propose this one as an example:\n![Workflow](./docs/img/schemas-workflow.jpg)\n\n## Status\n\n> ⚠️ Although the project is considered stable \n> please keep in mind that LabFunctions is still under active development\n> and therefore full backward compatibility is not guaranteed before reaching v1.0.0., APIS could change.\n\n\n## Features\n\nSome features can be used standalone, and others depend on each other.\n\n| Feature             | Status |  Note   |\n| --------------------| ------ | ------- |\n| Notebook execution  | Stable |  - |\n| Workflow scheduling | Beta   | This allow to schedule: every hour, every day, etc |\n| Build Runtimes      | Beta   | Build OCI compliance continers (Docker) and store it. | \n| Runtimes templates  | Stable | Genereate Dockerfile based on templates\n| Create and destroy servers | Alpha | Create and delete Machines in different cloud providers |\n| GPU Support | Beta | Allows to run workloads that requires GPU \n| Execution History | Alpha | Track notebooks & workflows executions |\n| Google Cloud support | Beta | Support google store and google cloud as provider |\n| Secrets managment | Alpha | Encrypt and manager private data in a project | \n| Project Managment | Alpha | Match each git repostiroy to a project |\n\n\n## Cluster options\n\nIt is possible to run different cluster configurations with custom auto scalling policies\n\n![GPU CLUSTER DEMO](https://media.giphy.com/media/OnhmnYiCJpe2FsTmaP/giphy.gif)\n\nInstances inside a cluster could be created manually or automatically\n\nSee a simple demo of a gpu cluster creation\n\n[https://www.youtube.com/watch?v=-R7lJ4dGI9s](https://www.youtube.com/watch?v=-R7lJ4dGI9s)\n\n\n## :earth_americas: Roadmap\n\nSee [Roadmap](/ROADMAP.md) *draft*\n\n## :post_office: Architecture\n\n![labfunctions architecture](/docs/img/platform-workflows.jpg)\n\n\n## :bookmark_tabs: References & inspirations\n- [Notebook Innovation - Netflix](https://netflixtechblog.com/notebook-innovation-591ee3221233)\n- [Tensorflow metastore](https://www.tensorflow.org/tfx/guide/mlmd)\n- [Maintainable and collaborative pipelines](https://blog.jupyter.org/ploomber-maintainable-and-collaborative-pipelines-in-jupyter-acb3ad2101a7)\n- [The magic of Merlin](https://shopify.engineering/merlin-shopify-machine-learning-platform)\n- [Scale aware approach](https://queue.acm.org/detail.cfm?id=3025012)\n- [\n\n\n## Contributing\n\nBug reports and pull requests are welcome on GitHub at the [issues\npage](https://github.com/labfunctions/labfunctions). This project is intended to be\na safe, welcoming space for collaboration, and contributors are expected to\nadhere to the [Contributor Covenant](http://contributor-covenant.org) code of\nconduct.\n\nPlease refer to [this\ndocument](https://github.com/dymaxionlabs/toolkit#dymaxion-labs-toolkit-charter)\nfor more details about our current governance model and formal committers\ngroup.\n\n## History\n\nLabfunctions was initially developed by [Xavier Petit](https://www.linkedin.com/in/xavier-petit-de-meurville-90200b41/) in the context of the needs of [algorinfo.com](https://algorinfo.com) and inspired by the following posts:  [Netflix](https://netflixtechblog.com/notebook-innovation-591ee3221233) and [Maintainable and collaborative pipelines](https://blog.jupyter.org/ploomber-maintainable-and-collaborative-pipelines-in-jupyter-acb3ad2101a7), during the second half of 2021. \n\nThe common cycle of work before the idea of labfunctions was to start exploring and prototyping models and processes in Jupyter Notebooks and then migrate those notebooks to packages and modules in python, finally the code was deployed as containers into production. \n\nAt that time the problem to solve was to reduce the step required from notebooks to production, then labfunctions emerge first as a module in the context of [dataproc](https://github.com/algorinfo/dataproc) using Sanic, RQ and Papermill as main libraries to orchestrate and execute notebooks as workflows.  \n\nIn 2022 Xavier Petit started working as a freelancer in [DymaxionLabs](https://dymaxionlabs.com/). They have a similar problem to be solved, but with two extra requirements: notebooks should be reproducible, and workloads usually require GPU hardware that should be provisioned on demand. With those two needs in mind, labfunctions was born adding: the idea of a “project” which match to a  Git Repository, the builds of docker containers (called runtimes in labfunctions) and the option to create servers on demand, each step with GPU support.   \n\n\n\n## License\n\nThis project is licensed under Apache 2.0. Refer to\n[LICENSE.txt](https://github.com/labfunctions/labfunctions/blob/main/LICENSE).\n",
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
    "python_requires": ">=3.8,<3.11",
}


setup(**setup_kwargs)
