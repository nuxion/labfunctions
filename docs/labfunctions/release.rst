Release
========

This document describes how to make a release.

There are two types of release:
A **pre release** instance, and a **final** one which includes a new release/* branch in github.

Pre release
---------------

1. Update the version number

The version field of pyproject.yaml is the source of truth for the entire process.
Then it should be updated because this value is needed by the rest of scripts to perform the release.

poetry version command can be used for this:
   
.. code-block:: bash

                poetry version prerelease


After this, update_versions.sh script should be run. This script updates the version in __version__.py which is used internally by the package between others:

.. code-block:: bash

                ./scripts/update_versions.sh


.. note::

   The two previous steps can be performed all together running `make preversion` command


2. Build python package and lock dependecies

After version update, the python package should be rebuilt

.. code-block:: bash

                make build

This step will update setup.py file, lock dependecies into requirements/ folder, and build the wheel package.

.. note::

   After this, the pre release package could be published into pypi using `make publish`
   This will publish the package as a pre-release version into the officials pypi servers.

   Alternatively you can use `make publish-test` to use pypi test infra instead.


3. Dockers build

Finally docker images could be updated. It's important to note that there are 3 kind of images:

* docker-all (client and server)
* docker-client-gpu (client with gpu support)
* docker-client (cpu only)

Regenerate all together:


.. code-block:: bash

                make generate-docker


.. note::

   make generate-docker uses `lab runtimes` command.
   This allows customization over the Dockerfiles generated.

                
After this, each docker image should be built and published:

.. code-block:: bash

                make docker-client
                make docker-client-push
 


