import os
import pathlib
import subprocess


def execute(cmd):
    p = subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if not err:
        return out.decode().strip()
    raise AttributeError(err.decode())


def short_head_id():
    return execute("git rev-parse --short HEAD")


def zip_git_current() -> str:
    root = pathlib.Path(os.getcwd())
    project = str(root).rsplit("/", maxsplit=1)[-1]
    (root / ".nb_temp").mkdir(parents=True, exist_ok=True)
    output_file = f"{str(root)}/.nb_temp/{project}.CURRENT.zip"
    print(output_file)
    stash_id = execute("git stash create")
    execute(f"git archive -o {output_file} {stash_id}")
    return output_file


def zip_git_head() -> str:
    root = pathlib.Path(os.getcwd())
    project = str(root).rsplit("/", maxsplit=1)[-1]
    id_ = short_head_id()
    (root / ".nb_temp").mkdir(parents=True, exist_ok=True)
    output_file = f"{str(root)}/.nb_temp/{project}.HEAD-{currentid_}.zip"
    print(output_file)
    execute(f"git archive -o {output_file} HEAD")
    return output_file
