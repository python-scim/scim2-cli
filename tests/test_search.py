import json

import pytest
from werkzeug import Response

from scim2_cli import cli


@pytest.fixture
def httpserver(httpserver, simple_user_payload):
    def search_handler(request):
        if request.json.get("count") == 666:
            return Response({}, status=666, content_type="application/scim+json")

        return Response(
            json.dumps(
                {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                    "totalResults": 1,
                    "itemsPerPage": request.json.get("count", "invalid"),
                    "startIndex": request.json.get("startIndex", "invalid"),
                    "Resources": [simple_user_payload("all")],
                }
            ),
            status=200,
            content_type="application/scim+json",
        )

    httpserver.expect_request("/.search", method="POST").respond_with_handler(
        search_handler,
    )

    return httpserver


def test_stdin(runner, httpserver, simple_user_payload):
    """Test that JSON stdin is passed in the GET request."""
    payload = {"count": 99, "startIndex": 99}
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "search"],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output == {
        "totalResults": 1,
        "itemsPerPage": 99,
        "startIndex": 99,
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "Resources": [simple_user_payload("all")],
    }


def test_search_request_payload(runner, httpserver, simple_user_payload):
    """Test that most of the arguments are passed in the payload."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "search",
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
            "99",
            "--count",
            "99",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    json_output = json.loads(result.output)
    assert json_output == {
        "totalResults": 1,
        "itemsPerPage": 99,
        "startIndex": 99,
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "Resources": [simple_user_payload("all")],
    }


def test_scimclient_error(runner, httpserver, simple_user_payload):
    """Test scim2_client errors handling."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "search",
            "--count",
            "666",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Unexpected response status code: 666" in result.output
