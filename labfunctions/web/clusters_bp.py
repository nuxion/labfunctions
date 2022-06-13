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
from labfunctions.web.utils import get_cluster, get_scheduler2

clusters_bp = Blueprint("clusters", url_prefix="clusters", version=API_VERSION)


@clusters_bp.get("/get-clusters-spec")
@protected()
async def cluster_list(request):
    """
    List clusters in the config file
    """
    cluster = get_cluster(request)
    _clusters = cluster.cluster.list_clusters()
    clusters = [cluster.get_cluster(c).dict() for c in _clusters]
    return json(clusters)


@clusters_bp.post("/<cluster_name>")
@openapi.parameter("cluster_name", str, "path")
async def cluster_instance_create(request, cluster_name):
    scheduler = get_scheduler2(request)
    job = await scheduler.enqueue_instance_creation(cluster_name=cluster_name)
    return json(dict(jobid=job.execid))


@clusters_bp.delete("/<cluster_name>/<machine>")
@openapi.parameter("cluster_name", str, "path")
@openapi.parameter("machine", str, "path")
async def cluster_instance_destroy(request, cluster_name, machine):
    scheduler = get_scheduler2(request)
    job = await scheduler.enqueue_instance_destruction(
        machine, cluster_name=cluster_name
    )
    return json(dict(jobid=job.execid))


@clusters_bp.get("/<cluster_name>")
@openapi.parameter("cluster_name", str, "path")
async def cluster_instances_list(request, cluster_name):
    cc = get_cluster(request)
    instances = await cc.list_instances(cluster_name)
    return json(instances)
