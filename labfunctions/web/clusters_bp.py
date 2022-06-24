# pylint: disable=unused-argument
import pathlib
from typing import List, Optional

from pydantic.error_wrappers import ValidationError
from sanic import Blueprint, Sanic
from sanic.response import json
from sanic_ext import openapi

from labfunctions import cluster, types
from labfunctions.conf.server_settings import settings
from labfunctions.defaults import API_VERSION
from labfunctions.security.web import protected
from labfunctions.web.utils import get_cluster, get_scheduler2

clusters_bp = Blueprint("clusters", url_prefix="clusters", version=API_VERSION)


@clusters_bp.get("/get-clusters-spec")
@protected()
async def cluster_get_spec(request):
    """
    List clusters in the config file
    """
    cc = get_cluster(request)
    _clusters = cc.cluster.list_clusters()
    clusters = [cc.get_cluster(c).dict() for c in _clusters]
    return json(clusters)


@clusters_bp.post("/")
@openapi.body({"application/json": cluster.CreateRequest})
@protected()
async def cluster_instance_create(request):
    """Create a machine"""
    scheduler = get_scheduler2(request)
    req = cluster.CreateRequest(**request.json)
    job = await scheduler.enqueue_instance_creation(req)
    return json(dict(jobid=job._id), 202)


@clusters_bp.post("/<cluster_name>/<machine>/_agent")
@openapi.parameter("cluster_name", str, "path")
@openapi.parameter("machine", str, "path")
@openapi.body({"application/json": cluster.DeployAgentRequest})
@protected()
async def cluster_agent_deploy(request, cluster_name, machine):
    scheduler = get_scheduler2(request)
    req = cluster.DeployAgentRequest(**request.json)
    task = cluster.DeployAgentTask(
        machine_name=machine, cluster_name=cluster_name, **req.dict()
    )
    job = await scheduler.enqueue_deploy_agent(task)
    return json(dict(jobid=job._id))


@clusters_bp.delete("/<cluster_name>/<machine>")
@openapi.parameter("cluster_name", str, "path")
@openapi.parameter("machine", str, "path")
@protected()
async def cluster_instance_destroy(request, cluster_name, machine):
    scheduler = get_scheduler2(request)
    ctx = cluster.DestroyRequest(cluster_name=cluster_name, machine_name=machine)
    cc = get_cluster(request)
    machine = await cc.get_instance(machine)
    if machine:
        job = await scheduler.enqueue_instance_destruction(ctx)
        return json(dict(jobid=job._id), 202)
    else:
        return json(dict(jobid=None), 200)


@clusters_bp.get("/<cluster_name>")
@openapi.parameter("cluster_name", str, "path")
@protected()
async def cluster_instances_list(request, cluster_name):
    cc = get_cluster(request)
    instances = await cc.list_instances(cluster_name)
    return json(instances)
