Server Installation
=======================

Lab Functions is composed of several components. Some of them depends on the environment where one wants to run it, for instance a Store is required to keep projects bundles and notebooks executed, this store could be a simple `NGINX with a WebDav configuration <https://github.com/nuxion/labfunctions/blob/main/fileserver.conf>`_, a filesystem local store, a Google Store or a compatible S3 store. For this reason multiple installations are possible.

Here we will see a simple a configuration where only one server is involved.

.. warning::
    This is not a production ready installation.
    SSL is not configurated, Redis doesn't have any acl, password, and so on.
    We keep ports binded to localhost, however after running docker-compose
    you should check which ports are open if you are in an untrusted network. 

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
* Create a user
* Create an agent and get a token
* Start services

Preparations
---------------

If docker and docker compose are not installed and you have a debian compatible distribution, you can use `cloudscripts <https://github.com/nuxion/cloudscripts/>`_: ::

  curl -Ls https://raw.githubusercontent.com/nuxion/cloudscripts/main/install.sh | sh
  sudo cscli -i docker
  sudo cscli -i docker-compose
  # in case that you don't have git
  sudo cscli -i git

After we are shure that we have docker and docker-compose, we can get the code needed to bootstrap our Lab, to that we can get the last stable version or the development version. 
  
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

And then repeat the same steps. 
 
.. note::

   The auth system of Lab Functions uses JWT tokens, and as encryption algorithm it uses ECDSA Curve keys. To avoid more steps in the installation process the server creates their own keys and put it in a volume called `labsecrets:/app/.secrets`


Now, if we look our directory, we should have something like that

Inside docker-compose we will see the components mentioned before, optional a nginx is provided but we don't cover that here.

Environment
---------------

Instead of adding variables in `docker-compose.yaml` we will prepare a `.env.docker` file for this as follow: ::

  # Postgresql service configuration
  POSTGRES_PASSWORD=mySecretPassword
  POSTGRES_DB=labfunctions
  POSTGRES_USER=lab
  # Lab functions control plane and agent
  LF_SQL=postgresql://lab:mySecretPassword@postgres:5432/labfunctions
  LF_ASQL=postgresql+asyncpg://lab:mySecretPassword@postgres:5432/labfunctions
  LF_WORKFLOW_SERVICE="http://your-accessible-ip:8000"
  LF_WEB_REDIS=redis://publicredisip:6379/0
  LF_RQ_REDIS=redis://publicredisip:6379/2
  LF_JWT_PUBLIC=./secrets/ecdsa.pub.pem
  LF_JWT_PRIVATE=./secrets/ecdsa.priv.pem
  LF_LOG=INFO
  LF_AGENT_TOKEN=_agent_generated_token
  LF_AGENT_REFRESH_TOKEN=_agent_refresh_token


Finally our /opt/labfunctions should looks something like that:

.. code-block:: bash

                tree -a -L 2
                .
                ├── .env.docker
                ├── docker-compose.yml
                └── scripts


Starting up services
---------------------

Our recommendations here is that you start service by service


1. Start postgresql
   
.. code-block:: bash

                docker-compose up -d postgres
                docker-compose logs postgres

   
2. Start redis

.. code-block:: bash

                docker-compose up -d redis
                docker-compose logs redis


3. Apply migrations, because is the firstime, also it will create the tables needed


.. code-block:: bash

                ./scripts/runcli
                lab manager db upgrade


4. Create a user, an agent and get the token

.. code-block:: bash

                ./scripts/runcli
                # create a user with admin permissions
                lab manager users -S create
                Username: nuxion
                Password:
                Password (repeat):
                Email (optional):
                Congrats!! user nuxion created

   
                
5. Now, we can start our control-plane:


.. code-block:: bash

                docker-compose up -d control-plane
                docker-compose logs control-plane



6. Before starting our agent service, we need to create a user agent and get their token 
   
.. code-block:: bash

                lab manager agent create -A
                {
                "username": "agt8iAWb-5SSdMhJX",
                "scopes": [
                    "agent:r:w",
                    "admin:r"
                ],
                "jwt": {
                    "access_token": "...",
                    "refresh_token": "..."
                }
                }

Then we should add access_token and refresh_token to `.env.docker` ::

  LF_AGENT_TOKEN=_agent_generated_token
  LF_AGENT_REFRESH_TOKEN=_agent_refresh_token

The last step before we can start our agent requires that the agent has access to /var/run/docker.sock

For that purpose, we should check in the docker-compose.yaml file, that the agent container starts with the same group id that docker has in the operating system. 

.. code-block:: yaml
                
                agent:
                  image: nuxion/labfunctions:{{ data.version }}
                  env_file: .env.docker
                  environment:
                    LF_SERVER: true
                  user: 1089:<group_id_of_docker>
                  command: >
                    lab agent run --qnames cpu,build,control -m local/ba/example
                  volumes:
                    - /var/run/docker.sock:/var/run/docker.sock
                    - labsecrets:/app/.secrets
                    - labstore:/app/.nb_tmp
 
  
7. And, finally we can start the agent:

.. code-block:: bash

                docker-compose up -d agent
                docker-compose logs agent



Reverse Proxy (Optional)
-------------------------

Good! The last step if we can to publish this as service, we need to add a reverse-proxy.

As an example, we provide a very very simple configuration using `Caddy Server <https://caddyserver.com/>`_. This will be the Caddyfile: ::

  <your domain>

  encode zstd gzip
  reverse_proxy 127.0.0.1:8000


.. note::

   If a real domain is provided Caddy will get a SSL certificate for you.
   TCP ports 80, 443 should be open, and root permissions are required.

Lastly, if you want that caddy keep running as service you should configured it as a SystemD service,
refer to https://caddyserver.com/docs/running#using-the-service
   
