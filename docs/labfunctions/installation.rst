Installation
=============

Lab Functions is composed of several components. Some of them depends on the environment where one wants to run it, for instance a Store is required to keep projects bundles and notebooks executed, this store could be a simple `NGINX with a WebDav configuration <https://github.com/nuxion/labfunctions/blob/main/fileserver.conf>`_, a filesystem local store, a Google Store or a compatible S3 store. For this reason multiple installations are possible.

Here we will see a simple a configuration where only one server is involved.

The requirments are:

* PostgreSQL >= 13
* Docker Registry V2
* Redis >= 5
* Docker & docker-compose

To avoid adding an extra component, the local store will be used, this add state to the server, then is not possible to scale to more servers. Also the Docker Registry could be ommited if the agent also runs in the server.

The steps will be:

* Get files need
* Prepare environmnet
* Init DB
* Create agent admin token
* Start services

Preparations
---------------

If docker and docker compose are not installed and you have a debian compatible distribution, you can use `cloudscripts <https://github.com/nuxion/cloudscripts/>`_: ::

  curl -Ls https://raw.githubusercontent.com/nuxion/cloudscripts/main/install.sh | sh
  sudo cscli -i docker
  sudo cscli -i docker-compose
  # in case that you don't have git
  sudo cscli -i git

Clone https://github.com/nuxion/labfunctions

To get the stable version: ::

  mkdir /opt/labfunctions
  cd /opt/labfunctions
  curl -sL https://github.com/nuxion/labfunctions/archive/refs/tags/0.8.0.tar.gz > labfunctions.tar.gz
  tar xvfz labfunctions.tar.gz
  cp -R labfunctions-0.8.0/scripts .
  cp labfunctions-0.8.0/docker-compose.yaml .
  rm labfunctions.tar.gz
  rm -R labfunctions-0.8.0

For the development version you can directly clone the main branch ::

  git clone --depth 1 https://github.com/nuxion/labfunctions labfunctions

After that we will need to create the ECDSA keys for the authentication system, then ::

  mkdir .secrets
  ./scripts/es512.sh

Now, if we look our directory, we should have something like that

.. code-block:: bash
                
                tree -a -L 2
                .
                ├── .secrets
                │   ├── ecdsa.priv.pem
                │   └── ecdsa.pub.pem
                ├── docker-compose.yml
                └── scripts

Inside docker-compose we will see the components mentioned before, optional a nginx is provided but we don't cover that here.

Environment
^^^^^^^^^^^^^

Instead of adding variable in `docker-compose.yaml` we will prepare a `.env.docker` file for this as follow: ::

  # Postgresql service configuration
  POSTGRES_PASSWORD=mySecretPassword
  POSTGRES_DB=labfunctions
  POSTGRES_USER=lab
  # Lab functions control plane and agent
  LF_SQL=postgresql://lab:mySecretPassword@postgres:5432/labfunctions
  LF_ASQL=postgresql+asyncpg://lab:mySecretPassword@postgres:5432/labfunctions
  LF_WEB_REDIS=redis://publicredisip:6379/0
  LF_RQ_REDIS=redis://publicredisip:6379/2
  LF_JWT_PUBLIC=secrets/ecdsa.pub.pem
  LF_JWT_PRIVATE=secrets/ecdsa.priv.pem
  LF_LOG=INFO

  








