import json

import pytest

from scim2_cli import cli

ERROR = {
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
    "status": "404",
    "detail": "Resource 1 not found",
}


@pytest.mark.parametrize(
    ("arguments", "method", "path"),
    [
        (["query", "user", "1"], "GET", "/Users/1"),
        (["query", "user"], "GET", "/Users"),
        (["search", "user"], "POST", "/Users/.search"),
        (["create", "user", "--user-name", "bjensen"], "POST", "/Users"),
        (
            ["replace", "user", "--id", "1", "--user-name", "bjensen"],
            "PUT",
            "/Users/1",
        ),
        (["modify", "user", "1", "remove", "nickName"], "PATCH", "/Users/1"),
        (["delete", "user", "1"], "DELETE", "/Users/1"),
        (["query", "--me"], "GET", "/Me"),
    ],
)
def test_error_responses_fail_the_command(runner, httpserver, arguments, method, path):
    """An error answered by the server is displayed on stdout, summed up on stderr, and fails the command."""
    httpserver.expect_oneshot_request(path, method=method).respond_with_json(
        ERROR, status=404, content_type="application/scim+json"
    )

    result = runner.invoke(cli, ["--url", httpserver.url_for("/"), *arguments])

    assert result.exit_code == 1, result.output
    assert json.loads(result.stdout) == ERROR
    assert result.stderr == "Error: 404 Resource 1 not found\n"


def test_error_without_detail(runner, httpserver):
    """An error without detail is summed up with its status."""
    error = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "status": "500",
    }
    httpserver.expect_oneshot_request("/Users/1").respond_with_json(
        error, status=500, content_type="application/scim+json"
    )

    result = runner.invoke(
        cli, ["--url", httpserver.url_for("/"), "query", "user", "1"]
    )

    assert result.exit_code == 1, result.output
    assert result.stderr == "Error: 500\n"


def test_success_does_not_fail_the_command(runner, httpserver, simple_user_payload):
    """A successful response leaves the command successful, with nothing on stderr."""
    httpserver.expect_oneshot_request("/Users/1").respond_with_json(
        simple_user_payload("1"), content_type="application/scim+json"
    )

    result = runner.invoke(
        cli, ["--url", httpserver.url_for("/"), "query", "user", "1"]
    )

    assert result.exit_code == 0, result.output
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("status", "content_type", "body"),
    [
        (404, "text/html", "<html>Not Found</html>"),
        (403, "text/plain", "Forbidden"),
        (404, "application/scim+json", ""),
        (401, "application/json", '{"error": "unauthorized"}'),
        (502, "text/html", "<html>Bad Gateway</html>"),
    ],
)
def test_failure_without_scim_error(runner, httpserver, status, content_type, body):
    """A failure without a SCIM error reports its HTTP status and fails the command."""
    httpserver.expect_oneshot_request("/Users/1").respond_with_data(
        body, status=status, content_type=content_type
    )

    result = runner.invoke(
        cli, ["--url", httpserver.url_for("/"), "query", "user", "1"]
    )

    assert result.exit_code == 1, result.output
    assert f"Error: The server answered {status} without a SCIM error" in result.output
