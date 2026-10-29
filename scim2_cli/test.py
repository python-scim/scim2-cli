import secrets
import sys

import click
from scim2_tester import Outcome
from scim2_tester import Status
from scim2_tester import check_server
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from .utils import DOC_URL
from .utils import Color
from .utils import escape_control_characters

OUTCOME_COLORS = {
    Outcome.PASSED: Color.green,
    Outcome.WARNING: Color.yellow,
    Outcome.FAILED: Color.red,
    Outcome.SKIPPED: Color.bright_black,
}
STATUS_WIDTH = max(len(status.name) for status in Status)


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
@click.option(
    "--strict",
    is_flag=True,
    help="Fail on deviations from the recommendations of the RFCs.",
)
@click.option(
    "--seed",
    type=int,
    help="Send the same generated values as the run that printed this seed.",
)
def test_cli(
    ctx: click.Context,
    verbose: bool,
    check_status_code: bool,
    check_content_type: bool,
    strict: bool,
    seed: int | None,
) -> None:
    """Perform a server SCIM compliance check using :doc:`scim2-tester <scim2_tester:index>`.

    .. code-block:: bash

         test
    """
    client = ctx.obj.client
    client.check_response_status_codes = check_status_code
    client.check_response_content_type = check_content_type
    if seed is None:
        seed = secrets.randbelow(2**32)
    results = check_server(client, seed=seed)
    click.echo(f"Performing a SCIM compliance check on {client.client.base_url} ...")
    failed = False
    for result in results:
        outcome = result.status.outcome
        if outcome is Outcome.FAILED or (strict and outcome is Outcome.WARNING):
            failed = True
        status = click.style(
            result.status.name.ljust(STATUS_WIDTH), fg=OUTCOME_COLORS[outcome]
        )
        label = " ".join(
            escape_control_characters(part)
            for part in (result.title, result.resource_type, result.attribute)
            if part
        )
        click.echo(f"{status} {label}")

        if result.reason:
            click.echo(f"  {escape_control_characters(result.reason)}")
            if verbose and result.data:
                click.echo(f"  {escape_control_characters(result.data)}")

    click.echo(f"Seed: {seed}")
    sys.exit(1 if failed else 0)
