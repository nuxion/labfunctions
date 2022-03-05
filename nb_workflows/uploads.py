import os
import pathlib
import subprocess
from typing import Optional, Union
from zipfile import ZipFile

from pydantic import BaseModel

from nb_workflows import secrets

TMP = ".nb_tmp"


class ProjectZipFile(BaseModel):
    filepath: str
    commit: Optional[str]
    current: Optional[bool] = False


def execute(cmd) -> str:
    with subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as p:

        out, err = p.communicate()
        if err:
            raise AttributeError(err.decode())

        return out.decode().strip()


def short_head_id():
    return execute("git rev-parse --short HEAD")


def zip_git_current(root) -> Union[ProjectZipFile, None]:
    """Zip the actual folder state
    using git stash, this should be used only when testing or developing
    """
    project = str(root).rsplit("/", maxsplit=1)[-1]
    (root / TMP).mkdir(parents=True, exist_ok=True)
    output_file = f"{str(root)}/{TMP}/{project}.CURRENT.zip"
    stash_id = execute("git stash create")
    execute(f"git archive -o {output_file} {stash_id}")
    return ProjectZipFile(filepath=output_file, current=True)


def zip_git_head(root) -> ProjectZipFile:
    """Zip the head of the repository.
    Not commited files wouldn't included in this zip file
    """
    project = str(root).rsplit("/", maxsplit=1)[-1]
    id_ = short_head_id()
    (root / TMP).mkdir(parents=True, exist_ok=True)
    output_file = f"{str(root)}/{TMP}/{project}.HEAD-{id_}.zip"
    execute(f"git archive -o {output_file} HEAD")
    return ProjectZipFile(filepath=output_file, commit=id_)


def zip_project(private_key, vars_file, current=False) -> ProjectZipFile:
    """Make a zip of this project.
    It uses git to skip files in the .gitignore file.
    After making the zip file with git,  it will add a secret file
    with the values of "[filename].nbvars" encrypted on it.

    :param dev: default False, if True it will make a git stash
    of the current files. If False, then will zip the last commited changes.
    """
    root = pathlib.Path(os.getcwd())
    zfile = None
    if current:
        zfile = zip_git_current(root)
    if not zfile:
        zfile = zip_git_head(root)

    secrets_file = secrets.write_secrets(root / TMP, private_key, vars_file)

    with ZipFile(zfile.filepath, "w") as zo:
        zo.write(secrets_file)

    pathlib.Path(secrets_file).unlink(missing_ok=True)
    return zfile
