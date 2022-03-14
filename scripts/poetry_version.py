import toml

package_name = "nb_workflows-0.7.0a0-py3-none-any"
package_name = "nb_workflows-{}"
# -py3-none-any

with open("pyproject.toml", "r", encoding="utf-8") as f:
    data = toml.loads(f.read())

version = data["tool"]["poetry"]["version"]
if "alpha" in version:
    _ver = version.split("-")[0]
    alpha = version.rsplit(".", maxsplit=1)[1]
    print(package_name.format(f"{_ver}a{alpha}"))
else:
    print(package_name.format(version))
