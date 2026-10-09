import json

import pytest
from scim2_models import Group
from scim2_models import ResourceType
from scim2_models import User

from scim2_cli import cli

PATCH_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"
USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"


@pytest.fixture
def invoke(runner, httpserver):
    def wrapped(*arguments, **kwargs):
        return runner.invoke(
            cli, ["--url", httpserver.url_for("/"), *arguments], **kwargs
        )

    return wrapped


@pytest.fixture
def invoke_with_groups(runner, httpserver, tmp_path):
    """Invoke the CLI on a server serving users and groups."""
    schemas = tmp_path / "schemas.json"
    schemas.write_text(
        json.dumps([User.to_schema().model_dump(), Group.to_schema().model_dump()])
    )
    resource_types = tmp_path / "resource_types.json"
    resource_types.write_text(
        json.dumps(
            [
                ResourceType(
                    id="User", name="User", endpoint="/Users", schema_=USER_SCHEMA
                ).model_dump(),
                ResourceType(
                    id="Group", name="Group", endpoint="/Groups", schema_=GROUP_SCHEMA
                ).model_dump(),
            ]
        )
    )

    def wrapped(*arguments, **kwargs):
        return runner.invoke(
            cli,
            [
                "--url",
                httpserver.url_for("/"),
                "--schemas",
                str(schemas),
                "--resource-types",
                str(resource_types),
                *arguments,
            ],
            **kwargs,
        )

    return wrapped


def expect_patch(httpserver, path, operations, response=None):
    """Expect a patch request with the operations, answered with the response or without content."""
    handler = httpserver.expect_oneshot_request(
        path,
        method="PATCH",
        json={"schemas": [PATCH_SCHEMA], "Operations": operations},
    )
    if response is None:
        handler.respond_with_data(status=204)
    else:
        handler.respond_with_json(response, content_type="application/scim+json")


def test_replace(invoke, httpserver, simple_user_payload):
    """A replace operation is sent, and the modified resource is displayed."""
    expect_patch(
        httpserver,
        "/Users/1",
        [{"op": "replace", "path": "displayName", "value": "Barbara Jensen"}],
        simple_user_payload("1"),
    )

    result = invoke("modify", "user", "1", "replace", "displayName", "Barbara Jensen")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "1"


def test_no_content(invoke, httpserver):
    """Nothing is displayed when the server answers without content."""
    expect_patch(httpserver, "/Users/1", [{"op": "remove", "path": "displayName"}])

    result = invoke("modify", "user", "1", "remove", "displayName")

    assert result.exit_code == 0, result.output
    assert result.output == ""


def test_operations_are_sent_in_order(invoke, httpserver):
    """The operations are sent in the order of the command line (RFC 7644 §3.5.2)."""
    expect_patch(
        httpserver,
        "/Users/1",
        [
            {"op": "remove", "path": 'emails[type eq "work"]'},
            {"op": "add", "path": "emails", "value": [{"value": "b@example.com"}]},
            {"op": "replace", "path": "nickName", "value": "Babs"},
            {"op": "remove", "path": "title"},
        ],
    )

    result = invoke(
        "modify",
        "user",
        "1",
        "remove",
        'emails[type eq "work"]',
        "add",
        "emails",
        '[{"value": "b@example.com"}]',
        "replace",
        "nickName",
        "Babs",
        "remove",
        "title",
    )

    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    ("path", "value", "sent"),
    [
        ("nickName", "42", "42"),
        ("name.givenName", "true", "true"),
        ('emails[type eq "work"].value', "b@example.com", "b@example.com"),
        ("profileUrl", "https://example.com/bjensen", "https://example.com/bjensen"),
        ("active", "false", False),
        ("emails.primary", "true", True),
        ("name", '{"givenName": "Barbara"}', {"givenName": "Barbara"}),
        (
            'emails[type eq "work"]',
            '{"value": "b@example.com"}',
            {"value": "b@example.com"},
        ),
        ("emails", '[{"value": "b@example.com"}]', [{"value": "b@example.com"}]),
    ],
)
def test_values_are_typed_after_the_schema(invoke, httpserver, path, value, sent):
    """String values are sent as is, and the other values are read in JSON."""
    expect_patch(
        httpserver, "/Users/1", [{"op": "replace", "path": path, "value": sent}]
    )

    result = invoke("modify", "user", "1", "replace", path, value)

    assert result.exit_code == 0, result.output


def test_empty_path(invoke, httpserver):
    """An empty path applies a JSON object of attributes to the resource."""
    expect_patch(
        httpserver,
        "/Users/1",
        [{"op": "replace", "value": {"nickName": "Babs", "active": False}}],
    )

    result = invoke(
        "modify", "user", "1", "replace", "", '{"nickName": "Babs", "active": false}'
    )

    assert result.exit_code == 0, result.output


def test_operation_ignores_the_case(invoke, httpserver):
    """The operations can be typed with any case."""
    expect_patch(
        httpserver, "/Users/1", [{"op": "replace", "path": "nickName", "value": "Babs"}]
    )

    result = invoke("modify", "user", "1", "REPLACE", "nickName", "Babs")

    assert result.exit_code == 0, result.output


def test_invalid_json_value(invoke):
    """A value that is not a string is refused when it is not valid JSON."""
    result = invoke("modify", "user", "1", "replace", "active", "nope")

    assert result.exit_code == 1, result.output
    assert "Invalid JSON value for 'active'" in result.output


def test_unknown_operation(invoke):
    """An unknown operation is reported with the available ones."""
    result = invoke("modify", "user", "1", "move", "nickName", "Babs")

    assert result.exit_code == 1, result.output
    assert (
        "Unknown operation 'move'. Available values are: add, replace, remove"
        in result.output
    )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["replace", "nickName"], "The 'replace' operation takes a path and a value."),
        (["add"], "The 'add' operation takes a path and a value."),
        (["remove"], "The 'remove' operation takes a path."),
        (["remove", ""], "The 'remove' operation takes a path."),
    ],
)
def test_missing_operation_arguments(invoke, arguments, message):
    """An operation missing its path or its value is refused."""
    result = invoke("modify", "user", "1", *arguments)

    assert result.exit_code == 1, result.output
    assert message in result.output


def test_unknown_attribute(invoke):
    """An attribute the resource type does not have is refused."""
    result = invoke("modify", "user", "1", "replace", "unknown", "x")

    assert result.exit_code == 1, result.output
    assert "Unknown attributes: unknown" in result.output


def test_invalid_path(invoke):
    """A path with an invalid syntax is refused."""
    result = invoke("modify", "user", "1", "remove", "emails[")

    assert result.exit_code == 1, result.output
    assert "Invalid path 'emails[': invalid syntax at column 7" in result.output


def test_read_only_attribute(invoke):
    """An operation on a read-only attribute is refused before being sent."""
    result = invoke("modify", "user", "1", "replace", "id", "2")

    assert result.exit_code == 1, result.output
    assert "'id' is read-only" in result.output


def test_unknown_resource_type(invoke):
    """An unknown resource type is reported with the available ones."""
    result = invoke("modify", "invalid", "1", "remove", "nickName")

    assert result.exit_code == 1, result.output
    assert (
        "Unknown resource type 'invalid'. Available values are: user" in result.output
    )


@pytest.mark.parametrize("arguments", [[], ["user"]])
def test_missing_resource(invoke, arguments):
    """Without --me, a resource type and an id are needed."""
    result = invoke("modify", *arguments)

    assert result.exit_code == 1, result.output
    assert "Pass a resource type and an id, or --me." in result.output


def test_missing_operation(invoke):
    """At least one operation is needed."""
    result = invoke("modify", "user", "1")

    assert result.exit_code == 1, result.output
    assert "Missing operation." in result.output


def test_stdin(invoke, httpserver, simple_user_payload):
    """A patch operation passed to stdin is sent as is."""
    payload = {
        "schemas": [PATCH_SCHEMA],
        "Operations": [{"op": "replace", "value": {"nickName": "Babs"}}],
    }
    httpserver.expect_oneshot_request(
        "/Users/1", method="PATCH", json=payload
    ).respond_with_json(simple_user_payload("1"), content_type="application/scim+json")

    result = invoke("modify", "user", "1", input=json.dumps(payload))

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "1"


def test_stdin_and_operations(invoke):
    """The operations are passed either as arguments or to stdin."""
    result = invoke(
        "modify",
        "user",
        "1",
        "remove",
        "nickName",
        input=json.dumps({"schemas": [PATCH_SCHEMA], "Operations": []}),
    )

    assert result.exit_code == 1, result.output
    assert "Pass the operations either as arguments or to stdin." in result.output


def test_error_response(invoke, httpserver):
    """The error the server answers is displayed."""
    httpserver.expect_oneshot_request("/Users/1", method="PATCH").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": "Resource 1 not found",
        },
        status=404,
        content_type="application/scim+json",
    )

    result = invoke("modify", "user", "1", "remove", "nickName")

    assert json.loads(result.output)["detail"] == "Resource 1 not found"


def test_unexpected_response(invoke, httpserver):
    """A response that is not a SCIM message is reported."""
    httpserver.expect_oneshot_request("/Users/1", method="PATCH").respond_with_data(
        "<html>Internal Server Error</html>", status=500, content_type="text/html"
    )

    result = invoke("modify", "user", "1", "remove", "nickName")

    assert result.exit_code == 1, result.output
    assert "Error: Unexpected response content format" in result.output


def test_me(invoke, httpserver, simple_user_payload):
    """With --me, the operations are sent to /Me."""
    expect_patch(
        httpserver,
        "/Me",
        [{"op": "replace", "path": "active", "value": False}],
        simple_user_payload("me"),
    )

    result = invoke("modify", "--me", "replace", "active", "false")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "me"


def test_me_types_values_after_the_resource_type_with_the_attributes(
    invoke_with_groups, httpserver
):
    """With --me, the values are typed after the first resource type with the attributes."""
    expect_patch(
        httpserver,
        "/Me",
        [{"op": "add", "path": "members", "value": [{"value": "1"}]}],
    )

    result = invoke_with_groups("modify", "--me", "add", "members", '[{"value": "1"}]')

    assert result.exit_code == 0, result.output


def test_me_attributes_of_several_resource_types(invoke_with_groups):
    """With --me, the attributes must all belong to a same resource type."""
    result = invoke_with_groups(
        "modify", "--me", "remove", "members", "remove", "nickName"
    )

    assert result.exit_code == 1, result.output
    assert "No resource type has all the attributes: members, nickName" in result.output


@pytest.mark.parametrize("arguments", [["user"], ["user", "1"]])
def test_me_refuses_a_resource_type(invoke, arguments):
    """--me already designates a single resource."""
    result = invoke("modify", "--me", *arguments, "remove", "nickName")

    assert result.exit_code == 1, result.output
    assert "--me cannot be used with a resource type or an id." in result.output
