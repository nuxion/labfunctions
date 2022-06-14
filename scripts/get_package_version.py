import toml

# package_name = "labfunctions-0.7.0a0-py3-none-any"
# -py3-none-any


def get_version_poetry(poetry="pyproject.toml") -> str:
    """Get the version of the package from pyproject file"""
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        data = toml.loads(f.read())

    return data["tool"]["poetry"]["version"]


def package_version():
    """Normalize the name of the package for setup.py and pypi"""
    # "labfunctions-0.7.0a0-py3-none-any"
    version = get_version_poetry()
    ver_norm = version
    if "alpha" in version:
        _ver = version.split("-")[0]
        alpha = version.rsplit(".", maxsplit=1)[1]
        ver_norm = f"{_ver}a{alpha}"
    return ver_norm


if __name__ == "__main__":
    print(package_version())
