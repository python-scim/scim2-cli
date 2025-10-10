import json

from scim2_cli import cli


def test_no_command(runner, httpserver):
    """Test that no command displays the help."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "replace"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "replace user --help" in result.output


def test_invalid_command(runner, httpserver):
    """Test invalid command."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "replace", "invalid"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Error: Invalid model" in result.output


def test_no_command_stdin(runner, httpserver, simple_user_payload):
    """Test that JSON stdin is passed in the PUT request."""
    response_payload = simple_user_payload("old-user")
    httpserver.expect_request(
        "/Users/old-user",
        method="PUT",
    ).respond_with_json(
        response_payload,
        status=200,
        content_type="application/scim+json",
    )

    payload = {
        "id": "old-user",
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "old-user@example.com",
    }

    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "replace"],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    json_output = json.loads(result.output)

    assert json_output == response_payload


def test_no_command_payload_without_an_id(runner, httpserver, simple_user_payload):
    """Test that ids are needed."""
    payload = {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "old-user@example.com",
    }

    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "replace"],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Resource must have an id" in result.output


def test_no_command_no_stdin(runner, httpserver, simple_user_payload):
    """Test missing stdin."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "replace"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Usage: cli replace" in result.output


def test_no_command_scimclient_error(runner, httpserver, simple_user_payload):
    """Test scim2_client errors handling."""
    httpserver.expect_request(
        "/Users/old-user",
        method="PUT",
    ).respond_with_json(
        simple_user_payload("old-user"),
        status=999,
        content_type="application/scim+json",
    )

    payload = {
        "id": "old-user",
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "old-user@example.com",
    }

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "replace",
        ],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Unexpected response status code: 999" in result.output


def test_no_command_validation_error(runner, httpserver, simple_user_payload):
    """Test pydantic errors handling."""
    httpserver.expect_request(
        "/Users/old-user",
        method="PUT",
    ).respond_with_json(
        {"invalid": "json"},
        status=200,
        content_type="application/scim+json",
    )

    payload = {
        "id": "old-user",
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "old-user@example.com",
    }

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "replace",
        ],
        catch_exceptions=False,
        input=json.dumps(payload),
    )
    assert result.exit_code == 1, result.output
    assert "Expected type User but got undefined object with no schema" in result.output


def test_command_stdin(runner, httpserver, simple_user_payload):
    """Test that JSON stdin is passed in the PUT request."""
    response_payload = simple_user_payload("old-user")
    httpserver.expect_request(
        "/Users/old-user",
        method="PUT",
    ).respond_with_json(
        response_payload,
        status=200,
        content_type="application/scim+json",
    )

    payload = {
        "id": "old-user",
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "old-user@example.com",
    }

    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "replace", "user"],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    json_output = json.loads(result.output)

    assert json_output == response_payload


def test_command_parameters(runner, httpserver, simple_user_payload):
    """Test that parameters passed in the PUT request."""
    response_payload = simple_user_payload("old-user")
    httpserver.expect_request(
        "/Users/old-user",
        method="PUT",
    ).respond_with_json(
        response_payload,
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "replace",
            "user",
            "--id",
            "old-user",
            "--user-name",
            "old-user@example.com",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    json_output = json.loads(result.output)

    assert json_output == response_payload


def test_command_payload_without_an_id(runner, httpserver, simple_user_payload):
    """Test that ids are needed."""
    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "replace",
            "user",
            "--user-name",
            "old-user@example.com",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Resource must have an id" in result.output


def test_command_no_stdin_no_parameter(runner, httpserver, simple_user_payload):
    """No parameter and no stdin should display the help."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "replace", "user"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Usage: cli replace user" in result.output


def test_command_scimclient_error(runner, httpserver, simple_user_payload):
    """Test scim2_client errors handling."""
    httpserver.expect_request(
        "/Users/old-user",
        method="PUT",
    ).respond_with_json(
        simple_user_payload("old-user"),
        status=999,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "replace",
            "user",
            "--id",
            "old-user",
            "--user-name",
            "old-user@example.com",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Unexpected response status code: 999" in result.output


def test_command_validation_error(runner, httpserver, simple_user_payload):
    """Test pydantic errors handling."""
    httpserver.expect_request(
        "/Users/old-user",
        method="PUT",
    ).respond_with_json(
        {"invalid": "json"},
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "replace",
            "user",
            "--id",
            "old-user",
            "--user-name",
            "old-user@example.com",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Expected type User but got undefined object with no schema" in result.output
