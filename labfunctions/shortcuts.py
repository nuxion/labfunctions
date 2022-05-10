# Shortcuts for client or agents only
from labfunctions import secrets
from labfunctions.client.shortcuts import from_env, from_file
from labfunctions.conf.utils import load_client as conf_loader

settings = conf_loader()
secrets = secrets.load(settings.BASE_PATH)
client = from_env(settings)
