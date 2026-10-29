from unittest.mock import patch

import click
import pytest
from scim2_tester import CheckResult
from scim2_tester import Outcome
from scim2_tester import Status

from scim2_cli import cli
from scim2_cli.test import OUTCOME_COLORS


def test_nominal(runner, httpserver):
    """Test SCIM compliance test."""
    results = [
        CheckResult(
            status=Status.SUCCESS,
            title="test1",
            description="description1",
            reason="reason1",
            data="data1",
        ),
        CheckResult(
            status=Status.ERROR,
            title="test2",
            description="description2",
            data="data2",
        ),
    ]
    with patch("scim2_cli.test.check_server", side_effect=[results]) as check_server:
        result = runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "test"],
            catch_exceptions=False,
        )
        seed = check_server.call_args.kwargs["seed"]

        expected_output = f"""Performing a SCIM compliance check on http://localhost:{httpserver.port}/ ...
SUCCESS    test1
  reason1
ERROR      test2
Seed: {seed}
"""
        assert result.output == expected_output


def test_verbose(runner, httpserver):
    """Test SCIM compliance test."""
    results = [
        CheckResult(
            status=Status.SUCCESS,
            title="test1",
            description="description1",
            reason="reason1",
            data="data1",
        ),
        CheckResult(
            status=Status.ERROR,
            title="test2",
            description="description2",
            reason="reason2",
            data="data2",
        ),
    ]
    with patch("scim2_cli.test.check_server", side_effect=[results]) as check_server:
        result = runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "test", "--verbose"],
            catch_exceptions=False,
        )
        seed = check_server.call_args.kwargs["seed"]

        expected_output = f"""Performing a SCIM compliance check on http://localhost:{httpserver.port}/ ...
SUCCESS    test1
  reason1
  data1
ERROR      test2
  reason2
  data2
Seed: {seed}
"""
        assert result.output == expected_output


def test_failure(runner, httpserver):
    """Test SCIM compliance test failure."""
    result = runner.invoke(
        cli,
        ["--url", "http://scim.invalid", "test"],
    )
    assert result.exit_code == 1, result.output


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ([], True),
        (["--dont-check-status-code", "--dont-check-content-type"], False),
    ],
)
def test_response_checks_options(runner, httpserver, options, expected):
    """Test that the response check options are applied on the client."""
    checked = {}

    def check_server(client, seed):
        checked["status_codes"] = client.check_response_status_codes
        checked["content_type"] = client.check_response_content_type
        return []

    with patch("scim2_cli.test.check_server", check_server):
        result = runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "test", *options],
            catch_exceptions=False,
        )

    assert result.exit_code == 0, result.output
    assert checked == {"status_codes": expected, "content_type": expected}


def run_checks(runner, httpserver, results, *options, color=False):
    with patch("scim2_cli.test.check_server", side_effect=[results]):
        return runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "test", *options],
            catch_exceptions=False,
            color=color,
        )


def test_resource_type_and_attribute(runner, httpserver):
    """Each result shows its resource type and its attribute when it has them."""
    results = [
        CheckResult(status=Status.SUCCESS, title="discovery_methods"),
        CheckResult(
            status=Status.SUCCESS, title="object_creation", resource_type="User"
        ),
        CheckResult(
            status=Status.SUCCESS,
            title="check_replace_attribute",
            resource_type="User",
            attribute="name.familyName",
        ),
    ]

    result = run_checks(runner, httpserver, results)

    assert result.output.splitlines()[1:-1] == [
        "SUCCESS    discovery_methods",
        "SUCCESS    object_creation User",
        "SUCCESS    check_replace_attribute User name.familyName",
    ]


@pytest.mark.parametrize(
    ("status", "exit_code"),
    [
        (Status.SUCCESS, 0),
        (Status.COMPLIANT, 0),
        (Status.ACCEPTABLE, 0),
        (Status.SKIPPED, 0),
        (Status.DEVIATION, 0),
        (Status.ERROR, 1),
        (Status.CRITICAL, 1),
    ],
)
def test_only_failures_fail_the_command(runner, httpserver, status, exit_code):
    """The command fails on errors and critical results only."""
    results = [CheckResult(status=status, title="check")]

    result = run_checks(runner, httpserver, results)

    assert result.exit_code == exit_code, result.output


@pytest.mark.parametrize(
    ("status", "exit_code"),
    [
        (Status.SUCCESS, 0),
        (Status.SKIPPED, 0),
        (Status.DEVIATION, 1),
        (Status.ERROR, 1),
    ],
)
def test_strict_fails_on_deviations(runner, httpserver, status, exit_code):
    """With --strict, the command also fails on deviations."""
    results = [CheckResult(status=status, title="check")]

    result = run_checks(runner, httpserver, results, "--strict")

    assert result.exit_code == exit_code, result.output


@pytest.mark.parametrize(
    ("status", "color"),
    [
        (Status.SUCCESS, "\x1b[32m"),
        (Status.ACCEPTABLE, "\x1b[32m"),
        (Status.DEVIATION, "\x1b[33m"),
        (Status.ERROR, "\x1b[31m"),
        (Status.CRITICAL, "\x1b[31m"),
        (Status.SKIPPED, "\x1b[90m"),
    ],
)
def test_status_color_follows_the_outcome(runner, httpserver, status, color):
    """Passing results are green, deviations yellow, failures red and skipped checks gray."""
    results = [CheckResult(status=status, title="check")]

    result = run_checks(runner, httpserver, results, color=True)

    assert f"{color}{status.name}" in result.output


def test_every_outcome_has_a_color():
    """Each outcome of scim2-tester has a color."""
    assert set(OUTCOME_COLORS) == set(Outcome)


def test_seed_is_sent_and_printed(runner, httpserver):
    """The seed passed with --seed generates the values, and is printed at the end."""
    with patch("scim2_cli.test.check_server", return_value=[]) as check_server:
        result = runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "test", "--seed", "1234"],
            catch_exceptions=False,
        )

    assert check_server.call_args.kwargs["seed"] == 1234
    assert result.output.splitlines()[-1] == "Seed: 1234"


def test_each_run_has_its_own_seed(runner, httpserver):
    """Without --seed, each run draws a new seed and prints it."""
    seeds = []
    for _ in range(2):
        with patch("scim2_cli.test.check_server", return_value=[]) as check_server:
            result = runner.invoke(
                cli,
                ["--url", httpserver.url_for("/"), "test"],
                catch_exceptions=False,
            )
        seed = check_server.call_args.kwargs["seed"]
        assert result.output.splitlines()[-1] == f"Seed: {seed}"
        seeds.append(seed)

    assert seeds[0] != seeds[1]


def test_seed_must_be_an_integer(runner, httpserver):
    """A seed that is not an integer is a usage error."""
    with patch("scim2_cli.test.check_server") as check_server:
        result = runner.invoke(
            cli, ["--url", httpserver.url_for("/"), "test", "--seed", "abc"]
        )

    assert result.exit_code == 2
    assert "'abc' is not a valid integer" in result.output
    check_server.assert_not_called()


def test_header_is_printed_before_the_checks(runner, httpserver):
    """The header is printed before the checks run."""

    def check_server(client, seed):
        click.echo("checks running")
        return []

    with patch("scim2_cli.test.check_server", check_server):
        result = runner.invoke(
            cli, ["--url", httpserver.url_for("/"), "test"], catch_exceptions=False
        )

    assert result.output.splitlines()[:2] == [
        f"Performing a SCIM compliance check on {httpserver.url_for('/')} ...",
        "checks running",
    ]
