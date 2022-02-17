# NB Workflows

![readthedocs](https://readthedocs.org/projects/nb_workflows/badge/?version=latest)
![PyPI - Format](https://img.shields.io/pypi/format/nb_workflows)
![PyPI - Status](https://img.shields.io/pypi/status/nb_workflows)


## Description 

If SQL is a lingua franca for querying data, Jupyter should be a lingua franca for data explorations, model training, and complex and unique tasks related to data. 

This workflow platform allows to run parameterized notebooks programmatically. Notebooks could be scheduled with cron syntax, by intervals, run by n times, only once or in time ranges (from 10am to 18pm).

So, the notebook is the main UI and the workflow job description.  

### Goal

Empowering different data roles in a project to put code into production, simplifying the time required to do so. It enables people to go from a data exploration instance to an entirely pipeline deployed in production, using the same notebook file made by a data scientist, analyst or whatever role working with data in an iterative way.

## How to run

```
# launch web process
# swagger by default: http://localhost:8000/docs/swagger 
make web 
```

```
# RQ Worker
make rqworker
```

```
# RQScheduler (optional)
make rqscheduler
```

## Architecture

![nb_workflows architecture](/docs/platform-workflows.jpg)

## References & inspirations
- [Notebook Innovation - Netflix](https://netflixtechblog.com/notebook-innovation-591ee3221233)
- [Tensorflow metastore](https://www.tensorflow.org/tfx/guide/mlmd)
- [Maintainable and collaborative pipelines](https://blog.jupyter.org/ploomber-maintainable-and-collaborative-pipelines-in-jupyter-acb3ad2101a7)

