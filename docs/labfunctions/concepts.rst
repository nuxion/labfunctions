Concepts
==========


Overview
---------

The main goal of Lab Functions is to reduce the stress of putting code into production, following good development practices that yield maintainable code, easy to debug, and quick to iterate. 

To follow that path, some practices are enforced such as the obligation by the user to generate a requirements.txt file, the recommendations of Git to version code, among others. But the central piece that allows most of the features of Lab Functions is the concept of a  **"runtime"** which uses container technology to package notebooks, isolate the environment, and execute them.

This is one of the possible paths in Lab functions:

.. image:: ../img/schemas-workflow.jpg
           :alt: Workflow example


Projects
---------

.. epigraph::
   
    There are only two hard things in Computer Science: cache invalidation and naming things.

    -- `Phil Karlton <https://martinfowler.com/bliki/TwoHardThings.html>`_


A project is essentially a way to **"name"** and **group** code, notebooks, variables, and so on.

Essentially it depends on the business problem to resolve, or to say it differently, it would depends on the `domain of the problem <https://en.wikipedia.org/wiki/Domain-driven_design>`_

In Lab Functions, a **Project** should match with a git repository, doing that we have a *root folder* and versioned code and **runtimes**. 

By default, when Lab Functions creates a project, it creates a root folder and puts files related to the project like a Dockerfile.default definition. Also it does other things behind the scenes like the creation of an agent user that will be in charge to run our workloads. 




Runtimes
-----------

Defining and generating a runtime could be cumbersome and hard to grasp in general. One of our goals is to simplify this process but some development knowledge is required.

The main idea and objective of a **Runtime** is to guarantee reproducibility in each execution of our code.
To do this we need to match operating system version, language version, software packages versions
and finally our own written code, among other things more subtle like folder structure, files permissions
and so on. A good tool that gives us almost all of this for free is docker, or more generally speaking:
containers.

Being very simplistic, we can say that a runtime is a **a box that gives us a controlled environment**
like a Scientist in a lab when *they* need to run a controlled experiment. Technically the **Runtime**
functionality wraps and manage the build, execution and versioning of the notebook’s code into
docker containers. 



Executions
------------

A execution is just that, our code/notebook put into a **runtime** and executed locally or remotly in the cloud. 

Each execution will produce a log and a output notebook. 


.. warning::
   Work in progress


Workflows
-----------

.. warning::
   Work in progress


Agents
----------

.. warning::
   Work in progress



Clusters
--------


.. warning::
   Work in progress

