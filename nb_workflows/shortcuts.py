# Shortcuts for client or agents only
from nb_workflows import secrets
from nb_workflows.client.shortcuts import from_env, from_file
from nb_workflows.conf.utils import load_client as conf_loader

settings = conf_loader()
secrets = secrets.load(settings.BASE_PATH)
client = from_env(settings)
