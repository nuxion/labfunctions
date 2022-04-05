import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from zipfile import ZipFile

from nb_workflows import secrets
from nb_workflows.conf import defaults
from nb_workflows.conf.jtemplates import get_package_dir, render_to_file
from nb_workflows.errors import CommandExecutionException
from nb_workflows.utils import execute_cmd

from .types import Credentials, ProjectZipFile

logger = logging.getLogger(__name__)


def generate_dockerfile(root, docker_options: Dict[str, Any]):
    render_to_file(
        "Dockerfile",
        str((root / defaults.DOCKERFILE_RUNTIME_NAME).resolve()),
        data=docker_options,
    )


def write_secrets(root, private_key, nbvars_dict) -> str:
    _vars = secrets.encrypt_nbvars(private_key, nbvars_dict)
    newline = "\n"
    encoded_vars = f'{newline.join(f"{key}={value}" for key, value in _vars.items())}'
    outfile = root / defaults.CLIENT_TMP_FOLDER / defaults.SECRETS_FILENAME
    with open(outfile, "w") as f:
        f.write(encoded_vars)

    return outfile


def git_short_head_id():
    return execute_cmd("git rev-parse --short HEAD")


def git_last_tag():
    return execute_cmd("git describe --tags")


def zip_git_current(
    root, prefix_folder=defaults.ZIP_GIT_PREFIX
) -> Union[ProjectZipFile, None]:
    """Zip the actual folder state
    using git stash, this should be used only when testing or developing
    """
    # project = str(root).rsplit("/", maxsplit=1)[-1]

    secrets_file = root / defaults.CLIENT_TMP_FOLDER / defaults.SECRETS_FILENAME

    filename = "CURRENT.zip"

    output_file = f"{str(root)}/{defaults.CLIENT_TMP_FOLDER}/{filename}"
    stash_id = execute_cmd("git stash create")
    if not stash_id:
        return None
    cmd = (
        f"git archive --prefix={prefix_folder} "
        f"--add-file {secrets_file} "
        f"-o {output_file} {stash_id} "
    )

    execute_cmd(cmd)

    return ProjectZipFile(
        filepath=output_file, filename=filename, current=True, version="current"
    )


def zip_git_head(root, prefix_folder=defaults.ZIP_GIT_PREFIX) -> ProjectZipFile:
    """Zip the head of the repository.
    Not commited files wouldn't included in this zip file
    """
    # project = str(root).rsplit("/", maxsplit=1)[-1]

    secrets_file = root / defaults.CLIENT_TMP_FOLDER / defaults.SECRETS_FILENAME

    tagname = None
    try:
        tagname = git_last_tag()
    except CommandExecutionException:
        logger.warning(
            "Any tag were found in the git repository, the last commit id will be used instad"
        )
    if not tagname:
        tagname = git_short_head_id()

    filename = f"{tagname}.zip"

    output_file = f"{str(root)}/{defaults.CLIENT_TMP_FOLDER}/{filename}"
    execute_cmd(
        f"git archive --prefix={prefix_folder} "
        f"--add-file {secrets_file} "
        f"-o {output_file} HEAD "
    )
    return ProjectZipFile(
        filepath=output_file, filename=filename, version=tagname.lower(), commit=tagname
    )


def zip_all(root, prefix_folder=defaults.ZIP_GIT_PREFIX):

    filename = "ALL.zip"

    output_file = f"{str(root)}/{defaults.CLIENT_TMP_FOLDER}/{filename}"
    secrets_file = Path(".") / defaults.CLIENT_TMP_FOLDER / defaults.SECRETS_FILENAME
    dst = root / ".secrets"
    dst.write_bytes(secrets_file.read_bytes())

    with ZipFile(output_file, "w") as z:
        for i in Path(".").glob("**/*"):
            if (
                not str(i).startswith(".venv")
                and not str(i).startswith(".git")
                and not str(i).startswith(".tox")
                and not str(i).startswith(defaults.CLIENT_TMP_FOLDER)
            ):
                if prefix_folder:
                    z.write(i, (prefix_folder / i))
                else:
                    z.write(i)

    dst.unlink(missing_ok=True)
    return ProjectZipFile(filepath=output_file, filename=filename, version="all")


def zip_project(root, secrets_file, current=False, all_=False) -> ProjectZipFile:
    """Make a zip of this project.
    It uses git to skip files in the .gitignore file.
    After making the zip file with git,  it will add a secret file
    with the values of "[filename].nbvars" encrypted on it.

    :param dev: default False, if True it will make a git stash
    of the current files. If False, then will zip the last commited changes.
    """

    # secrets_file = write_secrets(root, private_key, vars_file)

    zfile = None

    if current:
        zfile = zip_git_current(root)
        if not zfile:
            raise TypeError(
                "There isn't changes in the git repository to perform a "
                "CURRENT zip file. For untracked files you should add to "
                "the stash the changes, perform: git add ."
            )
    elif all_:
        zfile = zip_all(root)
    else:
        zfile = zip_git_head(root)

    return zfile


def manage_upload(privkey, env_file, current, all_=False) -> ProjectZipFile:
    """
    It manages how to upload project files to the server.

    Right now AGENT_TOKEN and AGENT_REFRESH_TOKEN are injected dinamically
    generating the keys on the server and puting it encrypted in the .secrets's file

    This is a little magical from the point of view of the user, but the intention is the
    simplification of the overall process, and we try to avoid that the user handle
    sensible information manually

    Same approach is taken with the private key to sign secrets. In the future this could
    change or at least we will provide to the user with the right mechanisms
    and documentation so that they can handle it manually if they want.
    """

    # secrets.nbvars["AGENT_TOKEN"] = creds.access_token
    # secrets.nbvars["AGENT_REFRESH_TOKEN"] = creds.refresh_token
    # checks if AGENT_TOKEN and REFERSH exist?

    root = Path(os.getcwd())
    (root / defaults.CLIENT_TMP_FOLDER).mkdir(parents=True, exist_ok=True)

    nbvars = secrets.load(str(root))

    secrets_file = write_secrets(root, privkey, nbvars)
    zfile = zip_project(root, secrets_file, current, all_)

    Path(secrets_file).unlink(missing_ok=True)

    return zfile
