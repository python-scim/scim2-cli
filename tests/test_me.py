import json

import pytest

from scim2_cli import cli

USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"


@pytest.fixture
def me(simple_user_payload):
    return simple_user_payload("me")


@pytest.fixture
def invoke(runner, httpserver):
    def wrapped(*arguments, **kwargs):
        return runner.invoke(
            cli, ["--url", httpserver.url_for("/"), *arguments], **kwargs
        )

    return wrapped


def respond(httpserver, method, payload, status=200, **kwargs):
    httpserver.expect_request("/Me", method=method, **kwargs).respond_with_json(
        payload, status=status, content_type="application/scim+json"
    )


def test_query(invoke, httpserver, me):
    """Query --me reads the resource of the authenticated client."""
    respond(httpserver, "GET", me)

    result = invoke("query", "--me")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "me"


def test_query_attributes(invoke, httpserver, me):
    """The attributes to return are sent with query --me."""
    respond(httpserver, "GET", me, query_string="attributes=userName")

    result = invoke("query", "--me", "--attribute", "userName")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "me"


def test_query_error(invoke, httpserver):
    """The error of a server without /Me is displayed (RFC 7644 §3.11)."""
    respond(
        httpserver,
        "GET",
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "501",
            "detail": "/Me is not supported",
        },
        status=501,
    )

    result = invoke("query", "--me")

    assert result.exit_code == 1, result.output
    assert json.loads(result.stdout)["status"] == "501"
    assert result.stderr == "Error: 501 /Me is not supported\n"


@pytest.mark.parametrize("arguments", [["user"], ["user", "1"]])
def test_query_refuses_a_resource_type(invoke, arguments):
    """--me already designates a single resource."""
    result = invoke("query", "--me", *arguments)

    assert result.exit_code == 1, result.output
    assert "--me cannot be used with a resource type or an id." in result.output


def test_query_refuses_listing_options(invoke):
    """--me designates a single resource, that cannot be paginated."""
    result = invoke("query", "--me", "--count", "10")

    assert result.exit_code == 1, result.output
    assert "--count cannot be used when querying a single resource." in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["create", "user", "--me", "--user-name", "me@example.com"],
        ["create", "--me", "user", "--user-name", "me@example.com"],
    ],
    ids=["subcommand-option", "command-option"],
)
def test_create(invoke, httpserver, me, arguments):
    """Create --me sends the resource to /Me."""
    respond(
        httpserver,
        "POST",
        me,
        status=201,
        json={"schemas": [USER_SCHEMA], "userName": "me@example.com"},
    )

    result = invoke(*arguments)

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "me"


def test_create_from_stdin(invoke, httpserver, me):
    """Create --me sends the payload passed to stdin to /Me."""
    payload = {"schemas": [USER_SCHEMA], "userName": "me@example.com"}
    respond(httpserver, "POST", me, status=201, json=payload)

    result = invoke("create", "--me", input=json.dumps(payload))

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "me"


@pytest.mark.parametrize(
    "arguments",
    [
        ["replace", "user", "--me", "--user-name", "me@example.com"],
        ["replace", "--me", "user", "--user-name", "me@example.com"],
        ["replace", "user", "--me", "--id", "me", "--user-name", "me@example.com"],
    ],
    ids=["subcommand-option", "command-option", "with-id"],
)
def test_replace(invoke, httpserver, me, arguments):
    """Replace --me sends the resource to /Me, with or without an id."""
    respond(httpserver, "PUT", me)

    result = invoke(*arguments)

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "me"


def test_replace_from_stdin(invoke, httpserver, me):
    """Replace --me sends the payload passed to stdin to /Me."""
    payload = {"schemas": [USER_SCHEMA], "userName": "me@example.com"}
    respond(httpserver, "PUT", me, json=payload)

    result = invoke("replace", "--me", input=json.dumps(payload))

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "me"


def test_delete(invoke, httpserver):
    """Delete --me deletes the resource of the authenticated client."""
    httpserver.expect_request("/Me", method="DELETE").respond_with_data(status=204)

    result = invoke("delete", "--me")

    assert result.exit_code == 0, result.output
    assert result.output == ""


@pytest.mark.parametrize("arguments", [["user"], ["user", "1"]])
def test_delete_refuses_a_resource_type(invoke, arguments):
    """--me already designates a single resource."""
    result = invoke("delete", "--me", *arguments)

    assert result.exit_code == 1, result.output
    assert "--me cannot be used with a resource type or an id." in result.output


@pytest.mark.parametrize("arguments", [[], ["user"]])
def test_delete_needs_a_resource(invoke, arguments):
    """Without --me, delete needs a resource type and an id."""
    result = invoke("delete", *arguments)

    assert result.exit_code == 1, result.output
    assert "Pass a resource type and an id, or --me." in result.output
