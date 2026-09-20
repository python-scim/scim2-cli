from unittest.mock import patch

import pytest
from scim2_tester import CheckResult
from scim2_tester import Status

from scim2_cli import cli


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
    with patch("scim2_cli.test.check_server", side_effect=[results]):
        result = runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "test"],
            catch_exceptions=False,
        )

        expected_output = f"""Performing a SCIM compliance check on http://localhost:{httpserver.port}/ ...
SUCCESS test1
  reason1
ERROR test2
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
    with patch("scim2_cli.test.check_server", side_effect=[results]):
        result = runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "test", "--verbose"],
            catch_exceptions=False,
        )

        expected_output = f"""Performing a SCIM compliance check on http://localhost:{httpserver.port}/ ...
SUCCESS test1
  reason1
  data1
ERROR test2
  reason2
  data2
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

    def check_server(client):
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
