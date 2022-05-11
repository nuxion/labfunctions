import toml


def get_version(poetry="pyproject.toml") -> str:
    """Get the version of the package from pyproject file"""
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        data = toml.loads(f.read())

    return data["tool"]["poetry"]["version"].strip()


if __name__ == "__main__":
    print(get_version())
