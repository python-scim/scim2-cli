import json

from scim2_cli import cli


def test_nominal_case(runner, httpserver):
    """Test deletion nominal case."""
    httpserver.expect_request(
        "/Users/ok",
        method="DELETE",
    ).respond_with_data(
        "",
        status=204,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "delete",
            "user",
            "ok",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output


def test_scimclient_error(runner, httpserver):
    """Test scim2_client errors handling."""
    httpserver.expect_request(
        "/Users/dummy-id",
        method="DELETE",
    ).respond_with_data(
        "",
        status=999,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "delete",
            "user",
            "dummy-id",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Unexpected response status code: 999" in result.output


def test_bad_resource_type(runner, httpserver):
    """Test passing an unknown resource type."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "delete",
            "invalid",
            "dummy-id",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Unknown resource type 'invalid'." in result.output


def test_not_found(runner, httpserver):
    """Test pydantic errors handling."""
    httpserver.expect_request(
        "/Users/unknown-id",
        method="DELETE",
    ).respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "detail": "Resource 2819c223-7f76-453a-919d-413861904646 not found",
            "status": "404",
        },
        status=404,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "delete",
            "user",
            "unknown-id",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    json_output = json.loads(result.output)
    assert json_output == {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": "Resource 2819c223-7f76-453a-919d-413861904646 not found",
        "status": "404",
    }
