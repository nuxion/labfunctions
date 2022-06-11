# pylint: disable=unused-argument
import pathlib
from typing import List, Optional

from pydantic.error_wrappers import ValidationError
from sanic import Blueprint, Sanic
from sanic.response import json
from sanic_ext import openapi

from labfunctions import types
from labfunctions.conf.server_settings import settings
from labfunctions.defaults import API_VERSION
from labfunctions.errors.generics import WorkflowRegisterError
from labfunctions.managers import projects_mg, runtimes_mg, workflows_mg
from labfunctions.security.web import protected
from labfunctions.utils import (
    get_query_param,
    parse_page_limit,
    run_async,
    secure_filename,
)

from .utils import get_cluster

clusters_bp = Blueprint("clusters", url_prefix="clusters", version=API_VERSION)


@clusters_bp.get("/")
@openapi.parameter("name", str, "path")
@protected()
def cluster_list(request, projectid):
    """
    List machines in the cluster
    """
    # pylint: disable=unused-argument

    # nb_files = list_workflows()
    nb_files = []

    return json(nb_files)


@clusters_bp.post("/<name>/_create")
@openapi.parameter("name", str, "path")
def cluster_instance_create(request, projectid):
    pass
