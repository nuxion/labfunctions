from zipfile import ZipFile

from nb_workflows.runtime import builder


def extract_project(project_zip_file, dst_dir):
    with ZipFile(project_zip_file, "r") as zo:
        zo.extractall(dst_dir)


def build(project_zip_file, temp_dir="/tmp/zip/", tag="nuxion/test-build"):
    extract_project(project_zip_file, temp_dir)
    builder.docker_build(f"{temp_dir}/src", "Dockerfile.nbruntime", tag=tag)
