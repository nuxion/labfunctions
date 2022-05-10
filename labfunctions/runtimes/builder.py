import json
import logging
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import httpx

import docker
from labfunctions import client, defaults
from labfunctions.commands import DockerCommand
from labfunctions.conf import load_client, load_server
from labfunctions.io.kvspec import GenericKVSpec

# from labfunctions.types.docker import DockerBuildLog, DockerBuildLowLog, DockerPushLog
from labfunctions.types.docker import DockerBuildLog
from labfunctions.types.runtimes import BuildCtx, RuntimeReq


def unzip_runtime(project_zip_file, dst_dir):
    with ZipFile(project_zip_file, "r") as zo:
        zo.extractall(dst_dir)


class BuildTask:
    def __init__(
        self,
        projectid: str,
        kvstore: GenericKVSpec,
        nbclient: Optional[client.nbclient.NBClient] = None,
        workflow_service: Optional[str] = None,
        agent_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.client = nbclient or client.agent(
            url_service=workflow_service,
            token=agent_token,
            refresh=refresh_token,
            projectid=projectid,
        )
        self.projectid = projectid
        self.kv = kvstore

    def get_runtime_file(self, full_zip_file_path, download_key_zip):
        with open(full_zip_file_path, "wb") as f:
            for chunk in self.kv.get_stream(download_key_zip):
                f.write(chunk)

    def run(self, ctx: BuildCtx) -> DockerBuildLog:
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_file = f"{tmp_dir}/{ctx.zip_name}"
            self.get_runtime_file(zip_file, ctx.download_zip)
            unzip_runtime(zip_file, tmp_dir)
            docker_tag = ctx.docker_name
            push = False
            if ctx.registry:
                docker_tag = f"{ctx.registry}/{docker_tag}"
                push = True
            # nb_client.events_publish(
            #    ctx.execid, f"Starting build for {docker_tag}", event="log"
            # )
            cmd = DockerCommand()
            logs = cmd.build(
                f"{tmp_dir}/src",
                f"{ctx.dockerfile}",
                tag=docker_tag,
                version=ctx.version,
                push=push,
            )

        return logs

    def register(self, ctx: BuildCtx):
        req = RuntimeReq(
            runtime_name=ctx.spec.name,
            docker_name=ctx.docker_name,
            spec=ctx.spec,
            project_id=ctx.projectid,
            version=ctx.version,
            registry=ctx.registry,
        )

        self.client.runtime_create(req)


def builder_exec(ctx: BuildCtx):
    """
    It will get the bundle file, build the container and register it
    """
    url_service = os.getenv("NB_WORKFLOW_SERVICE")
    access_token = os.getenv("NB_AGENT_TOKEN")
    refresh_token = os.getenv("NB_AGENT_REFRESH_TOKEN")

    kv = GenericKVSpec.create(ctx.project_store_class, ctx.project_store_bucket)
    task = BuildTask(
        ctx.projectid,
        kvstore=kv,
        workflow_service=url_service,
        agent_token=access_token,
        refresh_token=refresh_token,
    )
    rsp = task.run(ctx)
    if not os.getenv("NB_RUN_LOCAL"):
        task.register(ctx)
    return rsp


# def builder_exec(ctx: BuildCtx):
#    """It's in charge of building docker images for projects"""
#
#    settings = load_server()
#
#    nb_client = client.agent(
#        url_service=settings.WORKFLOW_SERVICE,
#        token=settings.AGENT_TOKEN,
#        refresh=settings.AGENT_REFRESH_TOKEN,
#        projectid=ctx.projectid,
#    )
#    project_dir, tmp_dir = prepare_files(ctx, settings)
#
#    # pd = nb_client.projects_get()
#    docker_tag = ctx.docker_name
#    push = False
#    if ctx.registry:
#        docker_tag = f"{ctx.registry}/{docker_tag}"
#        push = True
#
#    nb_client.events_publish(
#        ctx.execid, f"Starting build for {docker_tag}", event="log"
#    )
#    logs = docker_build(
#        f"{tmp_dir}/src",
#        f"{ctx.dockerfile}",
#        tag=docker_tag,
#        version=ctx.version,
#        push=push,
#    )
#    req = RuntimeReq(
#        runtime_name=ctx.spec.name,
#        docker_name=ctx.docker_name,
#        spec=ctx.spec,
#        project_id=ctx.projectid,
#        version=ctx.version,
#        registry=ctx.registry,
#    )
#    nb_client.runtime_create(req)
#
#    nb_client.events_publish(ctx.execid, data="finished", event="result")
#    nb_client.events_publish(ctx.execid, data="exit", event="control")
#
#    return logs
