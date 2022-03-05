import os

import click


def init_cli():
    if os.environ.get("NB_SERVER", False):
        from nb_workflows.cmd.manager import managercli
        from nb_workflows.cmd.services import servicescli

        return click.CommandCollection(sources=[servicescli, managercli])
    else:
        from nb_workflows.cmd.project import projectcli
        from nb_workflows.cmd.workflows import workflowscli

        return click.CommandCollection(sources=[workflowscli, projectcli])
        # return click.CommandCollection(sources=[workflowscli])


cli = init_cli()

if __name__ == "__main__":
    cli()
