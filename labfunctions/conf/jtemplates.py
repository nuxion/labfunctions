import importlib.util
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_package_dir(pkg):
    spec = importlib.util.find_spec(pkg)
    return spec.submodule_search_locations[0]


env = Environment(
    loader=FileSystemLoader(f"{get_package_dir('labfunctions')}/conf/templates"),
    autoescape=select_autoescape(),
)


def render(filename, *args, **kwargs):
    tpl = env.get_template(filename)
    return tpl.render(*args, **kwargs)


def render_to_file(template, dst, *args, **kwargs):
    text = render(template, *args, **kwargs)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    return text
