# -*- coding: utf-8 -*-
from setuptools import setup

packages = [
    "nb_workflows",
    "nb_workflows.auth",
    "nb_workflows.client",
    "nb_workflows.cmd",
    "nb_workflows.conf",
    "nb_workflows.conf.templates",
    "nb_workflows.core",
    "nb_workflows.db",
    "nb_workflows.db.migrations",
    "nb_workflows.errors",
    "nb_workflows.executors",
    "nb_workflows.io",
    "nb_workflows.managers",
    "nb_workflows.types",
    "nb_workflows.web",
]

package_data = {"": ["*"]}

install_requires = [
    "Jinja2>=3.0.3,<4.0.0",
    "PyJWT>=2.1.0,<2.2.0",
    "PyYAML>=6.0,<7.0",
    "aiofiles>=0.8.0,<0.9.0",
    "aioredis[hiredis]>=2.0.1,<3.0.0",
    "click>=8.0.1,<9.0.0",
    "cloudpickle>=2.0.0,<3.0.0",
    "cryptography>=36.0.1,<37.0.0",
    "dateparser>=1.1.0,<2.0.0",
    "docker>=5.0.3,<6.0.0",
    "httpx>=0.22.0,<0.23.0",
    "ipykernel>=6.9.1,<7.0.0",
    "ipython>=8.1.1,<9.0.0",
    "jupytext>=1.13.0,<2.0.0",
    "loky>=3.0.0,<4.0.0",
    "nanoid>=2.0.0,<3.0.0",
    "nbconvert>=6.2.0,<7.0.0",
    "papermill>=2.3.3,<3.0.0",
    "pydantic>=1.9.0,<2.0.0",
    "pytz>=2021.1,<2022.0",
    "rq>=1.10.0,<2.0.0",
    "tqdm>=4.62.3,<5.0.0",
]

extras_require = {
    "fsspec": ["fsspec>=2022.2.0,<2023.0.0"],
    "server": [
        "uvloop>=0.16.0,<0.17.0",
        "sanic>=21.6.2,<22.0.0",
        "sanic-openapi>=21.6.1,<22.0.0",
        "sanic-ext>=21.9.0,<22.0.0",
        "sanic-jwt>=1.7.0,<2.0.0",
        "SQLAlchemy[asyncio]>=1.4.26,<2.0.0",
        "SQLAlchemy-serializer>=1.4.1,<2.0.0",
        "psycopg2-binary>=2.9.1,<3.0.0",
        "asyncpg>=0.24.0,<0.25.0",
        "alembic>=1.6.5,<2.0.0",
        "rq-scheduler>=0.11.0,<0.12.0",
    ],
}

entry_points = {"console_scripts": ["nb = nb_workflows.cli:cli"]}

setup_kwargs = {
    "name": "nb-workflows",
    "version": "0.7.0a0",
    "description": "Schedule parameterized notebooks programmatically using cli or a REST API",
    "long_description": "# NB Workflows\n\n[![nb-workflows](https://github.com/nuxion/nb_workflows/actions/workflows/main.yaml/badge.svg)](https://github.com/nuxion/nb_workflows/actions/workflows/main.yaml)\n![readthedocs](https://readthedocs.org/projects/nb_workflows/badge/?version=latest)\n![PyPI - Format](https://img.shields.io/pypi/format/nb_workflows)\n![PyPI - Status](https://img.shields.io/pypi/status/nb_workflows)\n\n[![codecov](https://codecov.io/gh/nuxion/nb_workflows/branch/main/graph/badge.svg?token=F025Y1BF9U)](https://codecov.io/gh/nuxion/nb_workflows)\n\n\n## Description \n\nIf SQL is a lingua franca for querying data, Jupyter should be a lingua franca for data explorations, model training, and complex and unique tasks related to data.\n\nNB Workflows is a library and a platform that allows you to run parameterized notebooks in a distributed way. \nA Notebook could be launched remotly on demand, or could be schedule by intervals or using cron syntax.\n\nInternally it uses [Sanic](https://sanicframework.org) as web server, [papermill](https://papermill.readthedocs.io/en/latest/) as notebook executor, an [RQ](https://python-rq.org/)\nfor task distributions and coordination. \n\n\n### Goal\n\n\nEmpowering different data roles in a project to put code into production, simplifying the time required to do so. It enables people to go from a data exploration instance to an entirely pipeline deployed in production, using the same notebook file made by a data scientist, analyst or whatever role working with data in an iterative way.\n\n\n### Features\n\n- Define a notebook like a function, and execute it on demand\n- Automatic Dockerfile generation. A project should share a unique environment\n- Docker building and versioning: it build and track each release. \n- Execution History, Notifications to Slack or Discord.\n\n\n## Starting\n\nClient: \n\n```\npip install nb-workflows==0.6.0\nnb startporject .\n```\n\nServer:\n```\npip install nb-workflows[server]==0.6.0\n```\n\n\n### Roadmap\n\nSee [Roadmap](/ROADMAP.md) *draft*\n\n## Architecture\n\n![nb_workflows architecture](/docs/platform-workflows.jpg)\n\n\n\n## References & inspirations\n- [Notebook Innovation - Netflix](https://netflixtechblog.com/notebook-innovation-591ee3221233)\n- [Tensorflow metastore](https://www.tensorflow.org/tfx/guide/mlmd)\n- [Maintainable and collaborative pipelines](https://blog.jupyter.org/ploomber-maintainable-and-collaborative-pipelines-in-jupyter-acb3ad2101a7)\n\n\n",
    "author": "nuxion",
    "author_email": "nuxion@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/nuxion/nb_workflows",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "extras_require": extras_require,
    "entry_points": entry_points,
    "python_requires": ">=3.8,<3.10",
}


setup(**setup_kwargs)
