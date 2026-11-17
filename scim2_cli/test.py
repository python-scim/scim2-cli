import json
import secrets
import sys
from collections import Counter

import click
from scim2_tester import CheckResult
from scim2_tester import Outcome
from scim2_tester import Status
from scim2_tester import get_all_available_tags
from scim2_tester import iter_check_server
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
OUTCOME_LABELS = {
    Outcome.PASSED: ("passed", "passed"),
    Outcome.WARNING: ("warning", "warnings"),
    Outcome.FAILED: ("failed", "failed"),
    Outcome.SKIPPED: ("skipped", "skipped"),
}
STATUS_WIDTH = max(len(status.name) for status in Status)


def summary(outcomes: Counter[Outcome], seed: int) -> str:
    """Count the results of each outcome, in the order of the outcomes."""
    counts = []
    for outcome in Outcome:
        count = outcomes[outcome]
        if not count:
            continue
        singular, plural = OUTCOME_LABELS[outcome]
        counts.append(f"{count} {plural if count > 1 else singular}")
    return f"{', '.join(counts) or 'no checks ran'} (seed {seed})"


def echo_text(result: CheckResult, verbose: int) -> None:
    """Print a result as a line of text, followed by its reason and its data."""
    outcome = result.status.outcome
    if not verbose and outcome in (Outcome.PASSED, Outcome.SKIPPED):
        return
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
    if verbose > 1 and result.data:
        click.echo(f"  {escape_control_characters(result.data)}")


def echo_jsonl(result: CheckResult) -> None:
    """Print a result as a JSON object on a single line."""
    payload = {
        "id": result.id,
        "title": result.title,
        "resource_type": result.resource_type,
        "attribute": result.attribute,
        "status": result.status.name,
        "outcome": result.status.outcome.name,
        "reason": result.reason,
        "tags": sorted(result.tags),
    }
    click.echo(json.dumps(payload))


@click.command(cls=make_rst_to_ansi_formatter(DOC_URL), name="test")
@click.pass_context
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Show every result with its reason. Pass it twice to also show the data.",
)
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
@click.option(
    "--include-tags",
    multiple=True,
    type=click.Choice(get_all_available_tags()),
    help="Only run the checks with one of these tags. Can be repeated.",
)
@click.option(
    "--exclude-tags",
    multiple=True,
    type=click.Choice(get_all_available_tags()),
    help="Skip the checks with one of these tags. Can be repeated.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "jsonl"]),
    default="text",
    show_default=True,
    help="Print the results as text, or as one JSON object per line.",
)
def test_cli(
    ctx: click.Context,
    verbose: int,
    check_status_code: bool,
    check_content_type: bool,
    strict: bool,
    seed: int | None,
    include_tags: tuple[str, ...],
    exclude_tags: tuple[str, ...],
    output_format: str,
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
    jsonl = output_format == "jsonl"
    click.echo(
        f"Performing a SCIM compliance check on {client.client.base_url} ...",
        err=jsonl,
    )
    results = iter_check_server(
        client,
        seed=seed,
        include_tags=set(include_tags) or None,
        exclude_tags=set(exclude_tags) or None,
    )
    failed = False
    outcomes: Counter[Outcome] = Counter()
    for result in results:
        outcome = result.status.outcome
        outcomes[outcome] += 1
        if outcome is Outcome.FAILED or (strict and outcome is Outcome.WARNING):
            failed = True
        if jsonl:
            echo_jsonl(result)
        else:
            echo_text(result, verbose)

    if failed:
        color = Color.red
    elif outcomes[Outcome.WARNING] or not outcomes:
        color = Color.yellow
    else:
        color = Color.green
    click.secho(summary(outcomes, seed), fg=color, err=jsonl)
    sys.exit(1 if failed else 0)
