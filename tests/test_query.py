import json

import pytest

from scim2_cli import cli


@pytest.fixture
def httpserver(httpserver, simple_user_payload):
    httpserver.expect_request(
        "/",
        method="GET",
    ).respond_with_json(
        {
            "totalResults": 1,
            "itemsPerPage": 10,
            "startIndex": 1,
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "Resources": [simple_user_payload("all")],
        },
        status=200,
        content_type="application/scim+json",
    )

    httpserver.expect_request(
        "/Users",
        query_string="attributes=userName%2CdisplayName&filter=userName+Eq+%22john%22&sortBy=userName&sortOrder=ascending&startIndex=1&count=10",
        method="GET",
    ).respond_with_json(
        {
            "totalResults": 1,
            "itemsPerPage": 10,
            "startIndex": 1,
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "Resources": [simple_user_payload("full-qs")],
        },
        status=200,
        content_type="application/scim+json",
    )

    httpserver.expect_request(
        "/Users",
        method="GET",
    ).respond_with_json(
        {
            "totalResults": 1,
            "itemsPerPage": 10,
            "startIndex": 1,
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "Resources": [simple_user_payload("all-users")],
        },
        status=200,
        content_type="application/scim+json",
    )

    httpserver.expect_request(
        "/Users/one-by-id",
        method="GET",
    ).respond_with_json(
        simple_user_payload("one-by-id"),
        status=200,
        content_type="application/scim+json",
    )

    httpserver.expect_request(
        "/Users/user-name-qs",
        query_string="attributes=userName",
        method="GET",
    ).respond_with_json(
        simple_user_payload("user-name-qs"),
        status=200,
        content_type="application/scim+json",
    )

    httpserver.expect_request(
        "/Users/invalid-status-code",
        method="GET",
    ).respond_with_json(
        simple_user_payload("invalid-status-code"),
        status=999,
        content_type="application/scim+json",
    )

    httpserver.expect_request(
        "/Users/validation-error",
        method="GET",
    ).respond_with_json(
        {"invalid": "json"},
        content_type="application/scim+json",
    )

    return httpserver


def test_all(runner, httpserver, simple_user_payload):
    """Test passing no resource and no id."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output == {
        "Resources": [
            {
                "id": "all",
                "meta": {
                    "created": "2010-01-23T04:56:22Z",
                    "lastModified": "2011-05-13T04:42:34Z",
                    "location": f"http://localhost:{httpserver.port}/Users/all",
                    "resourceType": "User",
                    "version": 'W\\/"3694e05e9dff590"',
                },
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                ],
                "userName": "all@example.com",
            },
        ],
        "itemsPerPage": 10,
        "schemas": [
            "urn:ietf:params:scim:api:messages:2.0:ListResponse",
        ],
        "startIndex": 1,
        "totalResults": 1,
    }


def test_no_indent(runner, httpserver):
    """The --no-indent option prints the response payload on a single line."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "--no-indent",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    output = result.output.rstrip("\n")
    assert "\n" not in output
    assert json.loads(output)["totalResults"] == 1


def test_get_by_id(runner, httpserver, simple_user_payload):
    """Test passing a resource and an id."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
            "one-by-id",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output == simple_user_payload("one-by-id")


def test_get_resources_without_id(runner, httpserver, simple_user_payload):
    """Test passing a resource and no id."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output == {
        "totalResults": 1,
        "itemsPerPage": 10,
        "startIndex": 1,
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "Resources": [simple_user_payload("all-users")],
    }


def test_stdin(runner, httpserver, simple_user_payload):
    """Test that JSON stdin is passed in the GET request."""
    payload = {"attributes": "userName"}
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "query", "user", "user-name-qs"],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output == simple_user_payload("user-name-qs")


def test_search_request_payload(runner, httpserver, simple_user_payload):
    """Test that most of the arguments are passed in the payload when listing resources."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
            "--attribute",
            "userName",
            "--attribute",
            "displayName",
            "--filter",
            'userName Eq "john"',
            "--sort-by",
            "userName",
            "--sort-order",
            "ascending",
            "--start-index",
            "1",
            "--count",
            "10",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output["Resources"] == [simple_user_payload("full-qs")]


def test_listing_options_on_a_single_resource(runner, httpserver):
    """Test that the listing arguments are refused when an id is passed."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
            "one-by-id",
            "--filter",
            'userName Eq "john"',
            "--count",
            "10",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert (
        "Error: --count, --filter cannot be used when querying a single resource."
        in result.output
    )


def test_listing_options_on_the_service_provider_config(runner, httpserver):
    """Test that the listing arguments are refused on the ServiceProviderConfig endpoint."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "serviceproviderconfig",
            "--filter",
            'userName Eq "john"',
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert (
        "Error: --filter cannot be used when querying a single resource."
        in result.output
    )


def test_unknown_resource_type(
    runner,
    httpserver,
):
    """Test passing an unkwnown resource type."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "invalid",
            "dummy-id",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert (
        "Unknown resource type 'invalid'. Available values are: user, schema, resourcetype, serviceproviderconfig"
        in result.output
    )


def test_scimclient_error(runner, httpserver, simple_user_payload):
    """Test scim2_client errors handling."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
            "invalid-status-code",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Unexpected response status code: 999" in result.output


def test_validation_error(runner, httpserver, simple_user_payload):
    """Test pydantic errors handling."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
            "validation-error",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Expected type User but got undefined object with no schema" in result.output


def test_service_provider_config(runner, httpserver):
    """Test querying the ServiceProviderConfig singleton endpoint."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "query", "serviceproviderconfig"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output["schemas"] == [
        "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"
    ]
    assert json_output["documentationUri"] == "https://scim.test"


@pytest.mark.parametrize("cursor", ["", "VZUTiyhEQJ94IR"])
def test_cursor(runner, httpserver, simple_user_payload, cursor):
    """The cursor is sent to read a page of a cursor-based pagination (RFC 9865)."""
    httpserver.expect_oneshot_request(
        "/Users", query_string=f"cursor={cursor}&count=1", method="GET"
    ).respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 2,
            "itemsPerPage": 1,
            "nextCursor": "YkU3OF86Pz0rGv",
            "Resources": [simple_user_payload("cursor")],
        },
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
            "--cursor",
            cursor,
            "--count",
            "1",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["nextCursor"] == "YkU3OF86Pz0rGv"


def test_cursor_on_a_single_resource(runner, httpserver):
    """A cursor is refused when an id is passed."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "query", "user", "1", "--cursor", ""],
        catch_exceptions=False,
    )

    assert result.exit_code == 1, result.output
    assert (
        "Error: --cursor cannot be used when querying a single resource."
        in result.output
    )


@pytest.mark.parametrize("arguments", [["user"], ["user", "1"]])
def test_unset_attributes_are_not_sent(
    runner, httpserver, simple_user_payload, arguments
):
    """Without --attribute and --excluded-attribute, the query string has none."""
    path = "/" + "/".join(["Users", *arguments[1:]])
    payload = (
        simple_user_payload("1")
        if len(arguments) > 1
        else {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 0,
            "Resources": [],
        }
    )
    httpserver.expect_oneshot_request(
        path, query_string="", method="GET"
    ).respond_with_json(payload, content_type="application/scim+json")

    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "query", *arguments],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert httpserver.log[-1][0].query_string == b""
