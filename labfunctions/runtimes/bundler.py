import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from zipfile import ZipFile

from labfunctions import defaults, secrets
from labfunctions.conf.jtemplates import get_package_dir, render_to_file
from labfunctions.errors import CommandExecutionException
from labfunctions.types.runtimes import ProjectBundleFile, RuntimeSpec
from labfunctions.utils import execute_cmd

from .utils import git_last_tag, git_short_head_id

logger = logging.getLogger(__name__)


def get_secrets_filepath(working_area: Path) -> Path:

    return working_area / defaults.CLIENT_TMP_FOLDER / defaults.SECRETS_FILENAME


def write_secrets(working_area, private_key, nbvars_dict) -> Path:
    _vars = secrets.encrypt_nbvars(private_key, nbvars_dict)
    newline = "\n"
    encoded_vars = f'{newline.join(f"{key}={value}" for key, value in _vars.items())}'
    outfile = get_secrets_filepath(working_area)
    with open(outfile, "w") as f:
        f.write(encoded_vars)

    return outfile


def zip_git_stash(
    root, working_area, runtime_name, prefix_folder=defaults.ZIP_GIT_PREFIX
) -> Union[ProjectBundleFile, None]:
    """Zip the actual folder state
    using git stash, this should be used only when testing or developing
    """
    # project = str(root).rsplit("/", maxsplit=1)[-1]

    secrets_file = get_secrets_filepath(working_area)

    filename = f"{runtime_name}.stash.zip"

    output_file = f"{str(working_area)}/{defaults.CLIENT_TMP_FOLDER}/{filename}"
    stash_id = execute_cmd("git stash create")
    if not stash_id:
        return None
    cmd = (
        f"git archive --prefix={prefix_folder} "
        f"--add-file {secrets_file} "
        f"-o {output_file} {stash_id} "
    )

    execute_cmd(cmd)

    return ProjectBundleFile(
        filepath=output_file,
        filename=filename,
        current=False,
        stash=True,
        version="stash",
        runtime_name=runtime_name,
    )


def zip_git_head(
    root, working_area, runtime_name, prefix_folder=defaults.ZIP_GIT_PREFIX
) -> ProjectBundleFile:
    """Zip the head of the repository.
    Not commited files wouldn't included in this zip file
    """
    # project = str(root).rsplit("/", maxsplit=1)[-1]

    secrets_file = get_secrets_filepath(working_area)

    tagname = None
    try:
        tagname = git_last_tag()
    except CommandExecutionException:
        logger.warning(
            "Any tag were found in the git repository, the last commit id will be used instad"
        )
    if not tagname:
        tagname = git_short_head_id()

    filename = f"{runtime_name}.{tagname}.zip"

    output_file = f"{str(working_area)}/{defaults.CLIENT_TMP_FOLDER}/{filename}"
    execute_cmd(
        f"git archive --prefix={prefix_folder} "
        f"--add-file {secrets_file} "
        f"-o {output_file} HEAD "
    )
    return ProjectBundleFile(
        runtime_name=runtime_name,
        filepath=output_file,
        filename=filename,
        version=tagname.lower(),
        commit=tagname,
    )


def zip_current(
    root, working_area, runtime_name, prefix_folder=defaults.ZIP_GIT_PREFIX
) -> ProjectBundleFile:

    filename = f"{runtime_name}.current.zip"

    output_file = f"{str(working_area)}/{defaults.CLIENT_TMP_FOLDER}/{filename}"

    secrets_file = get_secrets_filepath(working_area)
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
    return ProjectBundleFile(
        runtime_name=runtime_name,
        filepath=output_file,
        filename=filename,
        version="current",
        current=True,
    )


def bundle_project(
    working_area: Union[str, Path],
    spec: RuntimeSpec,
    privkey=None,
    stash=False,
    current=False,
) -> ProjectBundleFile:
    """
    It's in charge of bundle all the files needed to build a runtime.
    This bundle could be uploaded to the server or used to build a local docker image.

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
    wa = Path(working_area)

    if not (root / spec.container.requirements).is_file():
        raise KeyError("A requirements file is missing")

    (wa / defaults.CLIENT_TMP_FOLDER).mkdir(parents=True, exist_ok=True)

    nbvars = secrets.load(str(root))

    if privkey:
        secrets_file = write_secrets(wa, privkey, nbvars)

    zfile = None

    if stash and not current:
        zfile = zip_git_stash(root, wa, spec.name)
        if not zfile:
            raise TypeError(
                "There isn't changes in the git repository to perform a "
                "STASH zip file. For untracked files you should add to "
                "the stash the changes, perform: git add ."
            )
    elif current and not stash:
        zfile = zip_current(root, wa, spec.name)
    elif not current and not stash:
        zfile = zip_git_head(root, wa, spec.name)
    else:
        raise AttributeError("Bad option: current and stash are different options")

    if privkey:
        Path(secrets_file).unlink(missing_ok=True)

    return zfile
