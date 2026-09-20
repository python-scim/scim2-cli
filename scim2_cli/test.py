import sys

import click
from scim2_tester import Status
from scim2_tester import check_server
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from .utils import DOC_URL
from .utils import Color


@click.command(cls=make_rst_to_ansi_formatter(DOC_URL), name="test")
@click.pass_context
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
@click.option(
    "--check-status-code/--dont-check-status-code",
    is_flag=True,
    default=True,
    help="Fail on unexpected return codes.",
)
@click.option(
    "--check-content-type/--dont-check-content-type",
    is_flag=True,
    default=True,
    help="Fail on unexpected content types.",
)
def test_cli(ctx, verbose, check_status_code, check_content_type):
    """Perform a server SCIM compliance check using :doc:`scim2-tester <scim2_tester:index>`.

    .. code-block:: bash

         test
    """
    client = ctx.obj["client"]
    client.check_response_status_codes = check_status_code
    client.check_response_content_type = check_content_type
    results = check_server(client)
    click.echo(f"Performing a SCIM compliance check on {client.client.base_url} ...")
    success = True
    for result in results:
        if result.status == Status.SUCCESS:
            status = click.style(result.status.name, fg=Color.green)
        else:
            status = click.style(result.status.name, fg=Color.red)
            success = False
        click.echo(f"{status} {result.title}")

        if result.reason:
            click.echo(f"  {result.reason}")
            if verbose and result.data:
                click.echo(f"  {result.data}")

    sys.exit(0 if success else 1)
