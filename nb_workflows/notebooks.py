import nbformat
from nbconvert import NotebookExporter
from traitlets.config import Config


def read_notebook(path, version=4):
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
        note = nbformat.reads(data, as_version=version)
    return note


def clean_output(path, version=4):
    """
    Cleans notebooks outputs, for more info see:
    https://nbconvert.readthedocs.io/en/latest/api/preprocessors.html#nbconvert.preprocessors.ClearOutputPreprocessor
    https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html
    """
    c = Config()
    c.NotebookExporter.preprocessors = [
        "nbconvert.preprocessors.ClearOutputPreprocessor"
    ]

    exporter = NotebookExporter(config=c)

    note = read_notebook(path, version=version)
    exported, resources_dict = exporter.from_notebook_node(note)

    return exported, resources_dict
