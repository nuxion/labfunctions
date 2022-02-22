import click

from nb_workflows.cmd.manager import managercli
from nb_workflows.cmd.services import servicescli
from nb_workflows.cmd.workflows import workflowscli

cli = click.CommandCollection(sources=[servicescli, managercli, workflowscli])

if __name__ == "__main__":
    cli()
