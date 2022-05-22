Quickstart
===========

Here we cover how to create a project locally. 

.. note::

   This guide presume that you have a server already installed, if not check :doc:`/labfunctions/server_installation`



Client installation
--------------------

Thereis multiple ways to install labfunctions client. Here will be installing it in a `Virtual environment <https://realpython.com/python-virtual-environments-a-primer/>`_


.. code-block:: bash

                mkdir <our_project_dir>
                cd <our_project_dir>
                virtualenv .venv
                source .venv/bin/activate
                pip3 install labfunctions==0.8.0


.. warning::
   We recommend that you pin the package version because apis can change without notice and break your setup. You should do this until we got a stable version.


Start Project
--------------

In the same folder that the previous step, we need to initialize our project. This command will create the files and folders needed to run our notebooks. 

.. tip::
   
   You can set server URL with ::

     lab config set url_server https://myurl.com
     # verify running:
     lab config get url_service

     
.. code-block:: bash
                
                lab startproject .

It will ask you about the project name, user and so on. At the end it will print a command to test if all is working right, run it.

.. code-block:: bash

                lab exec notebook welcome --local -p TIMEOUT=5
                # after a few second you should see an output similar to:
                {
                "projectid": "13xbjnpshq",
                "execid": "tmptL9DgwEO",
                "wfid": "tmpcY9ocmtl",
                "name": "welcome",
                "params": {
                    "TIMEOUT": "5",
                    "WFID": "tmpcY9ocmtl",
                    "EXECID": "tmptL9DgwEO",
                    "NOW": "2022-05-16T15:30:31.172582"
                },
                "input_": "notebooks/welcome.ipynb",
                "error": false,
                "elapsed_secs": 7.79,
                "created_at": "2022-05-16T15:30:31.172582",
                "cluster": "default",
                "machine": "cpu",
                "runtime": "nuxion/labfunctions:0.8.0-alpha.8",
                "docker_name": null,
                "output_name": "tmpcY9ocmtl.welcome.tmptL9DgwEO.ipynb",
                "output_dir": "outputs/ok/20220516",
                "error_dir": "outputs/errors/20220516",
                "error_msg": null
                }


Congratulations all is working.

Runtime
---------

Now that we started our project and we run the notebook that comes as an example, the next logical step is deploing it into production.

But to do that, our notebook code needs a **Runtime**.

.. tip::

   The runtime concept could be complex, for more information refer to :ref:`Runtimes`
   

To build the default runtime provided by lab functions, the command is:

.. code-block:: bash

                lab runtimes build default --current
                => Bundling runtime default
                (x) requirements file missing from requirements.txt

If we see a message error like that, it is because we didn't export the packages dependencies of our project. Lab functions let you choose your prefered way to do it, but the final format should be a **requirements.txt** file.

If you are in a virtualenv and using pip, you can do:

.. code-block:: bash

                pip3 list --format=freeze > requirements.txt

After that, we can run again the same command:

.. code-block:: bash

                lab runtimes build default --current
                => Bundling runtime default
                => Bundle generated in /home/nuxion/.labfunctions/13xbjnpshq/.nb_tmp/default.current.zip
                => Succesfully uploaded file
                => Build task sent with execid: bld.T0iS8YjyYCZ9lO


.. warning::
    We are using the flag **--current** to build an untracked version of the project for simplicity, real use cases should include git to get versioned runtimes.
    

    


