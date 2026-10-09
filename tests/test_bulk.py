import json

import pytest
from scim2_models import Bulk
from scim2_models import ServiceProviderConfig

from scim2_cli import cli

BULK_REQUEST = {
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:BulkRequest"],
    "Operations": [
        {
            "method": "POST",
            "path": "/Users",
            "bulkId": "qwerty",
            "data": {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "bjensen@example.com",
            },
        }
    ],
}
BULK_RESPONSE = {
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:BulkResponse"],
    "Operations": [
        {
            "method": "POST",
            "bulkId": "qwerty",
            "location": "https://example.com/v2/Users/92b725cd9465",
            "version": 'W/"oY4m4wn58tkVjJxK"',
            "status": "201",
        }
    ],
}


@pytest.fixture
def invoke(runner, httpserver, tmp_path):
    """Invoke the CLI on a server with the given bulk capabilities."""

    def wrapped(*arguments, bulk=None, **kwargs):
        config = ServiceProviderConfig(
            bulk=bulk or Bulk(supported=True, max_operations=10, max_payload_size=10000)
        )
        path = tmp_path / "service_provider_config.json"
        path.write_text(json.dumps(config.model_dump()))
        return runner.invoke(
            cli,
            [
                "--url",
                httpserver.url_for("/"),
                "--service-provider-config",
                str(path),
                *arguments,
            ],
            **kwargs,
        )

    return wrapped


def test_bulk(invoke, httpserver):
    """The bulk request passed to stdin is sent, and the response is displayed."""
    httpserver.expect_oneshot_request(
        "/Bulk", method="POST", json=BULK_REQUEST
    ).respond_with_json(BULK_RESPONSE, content_type="application/scim+json")

    result = invoke("bulk", input=json.dumps(BULK_REQUEST))

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["Operations"][0]["status"] == "201"


def test_without_stdin(invoke):
    """Without a bulk request, the help is displayed."""
    result = invoke("bulk")

    assert result.exit_code == 1, result.output
    assert "Usage: cli bulk" in result.output


def test_bulk_not_supported(invoke):
    """A bulk request is not sent to a server that does not support bulk operations."""
    result = invoke(
        "bulk",
        bulk=Bulk(supported=False, max_operations=0, max_payload_size=0),
        input=json.dumps(BULK_REQUEST),
    )

    assert result.exit_code == 1, result.output
    assert "Error: The server does not support bulk requests" in result.output


def test_too_many_operations(invoke):
    """A bulk request over the limits of the server is not sent."""
    request = {**BULK_REQUEST, "Operations": BULK_REQUEST["Operations"] * 2}

    result = invoke(
        "bulk",
        bulk=Bulk(supported=True, max_operations=1, max_payload_size=10000),
        input=json.dumps(request),
    )

    assert result.exit_code == 1, result.output
    assert (
        "Error: Bulk requests are limited to 1 operations by the server"
        in result.output
    )


def test_error_response(invoke, httpserver):
    """The error the server answers is displayed."""
    httpserver.expect_oneshot_request("/Bulk", method="POST").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "413",
            "detail": "The size of the bulk operation exceeds the maxPayloadSize",
        },
        status=413,
        content_type="application/scim+json",
    )

    result = invoke("bulk", input=json.dumps(BULK_REQUEST))

    assert json.loads(result.output)["status"] == "413"
