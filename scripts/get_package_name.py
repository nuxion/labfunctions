import toml

# package_name = "nb_workflows-0.7.0a0-py3-none-any"
NBPKG = "nb_workflows-{}"
# -py3-none-any


def get_version_poetry(poetry="pyproject.toml") -> str:
    """Get the version of the package from pyproject file"""
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        data = toml.loads(f.read())

    return data["tool"]["poetry"]["version"]


def package_name():
    """Normalize the name of the package for setup.py and pypi"""
    # "nb_workflows-0.7.0a0-py3-none-any"
    version = get_version_poetry()
    pkg_norm = NBPKG.format(version)
    if "alpha" in version:
        _ver = version.split("-")[0]
        alpha = version.rsplit(".", maxsplit=1)[1]
        pkg_norm = NBPKG.format(f"{_ver}a{alpha}")
    return pkg_norm


if __name__ == "__main__":
    print(package_name())
