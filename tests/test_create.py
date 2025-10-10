import json

from scim2_cli import cli


def test_no_command(runner, httpserver):
    """Test that no command displays the help."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "create"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "create user --help" in result.output


def test_invalid_command(runner, httpserver):
    """Test invalid command."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "create", "invalid"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Error: Invalid model" in result.output


def test_no_command_stdin(runner, httpserver, simple_user_payload):
    """Test that JSON stdin is passed in the POST request."""
    response_payload = simple_user_payload("new-user")
    httpserver.expect_request("/Users", method="POST").respond_with_json(
        response_payload,
        status=201,
        content_type="application/scim+json",
    )

    payload = {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "new-user@example.com",
    }

    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "create"],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    json_output = json.loads(result.output)

    assert json_output == response_payload


def test_no_command_no_stdin(runner, httpserver, simple_user_payload):
    """Test missing stdin."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "create"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Usage: cli create" in result.output


def test_no_command_scimclient_error(runner, httpserver, simple_user_payload):
    """Test scim2_client errors handling."""
    httpserver.expect_request(
        "/Users",
        method="POST",
    ).respond_with_json(
        simple_user_payload("new-user"),
        status=999,
        content_type="application/scim+json",
    )

    payload = {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "new-user@example.com",
    }

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "create",
        ],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Unexpected response status code: 999" in result.output


def test_no_command_validation_error(runner, httpserver, simple_user_payload):
    """Test pydantic errors handling."""
    httpserver.expect_request(
        "/Users",
        method="POST",
    ).respond_with_json(
        {"invalid": "json"},
        status=201,
        content_type="application/scim+json",
    )

    payload = {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "new-user@example.com",
    }

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "create",
        ],
        catch_exceptions=False,
        input=json.dumps(payload),
    )
    assert result.exit_code == 1, result.output
    assert "Expected type User but got undefined object with no schema" in result.output


def test_command_stdin(runner, httpserver, simple_user_payload):
    """Test that JSON stdin is passed in the POST request."""
    response_payload = simple_user_payload("new-user")
    httpserver.expect_request("/Users", method="POST").respond_with_json(
        response_payload,
        status=201,
        content_type="application/scim+json",
    )

    payload = {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
        "userName": "new-user@example.com",
    }

    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "create", "user"],
        input=json.dumps(payload),
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    json_output = json.loads(result.output)

    assert json_output == response_payload


def test_command_parameters(runner, httpserver, simple_user_payload):
    """Test that parameters are passed in the POST request."""
    response_payload = simple_user_payload("new-user")
    httpserver.expect_request("/Users", method="POST").respond_with_json(
        response_payload,
        status=201,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "create",
            "user",
            "--user-name",
            "new-user@example.com",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    json_output = json.loads(result.output)

    assert json_output == response_payload


def test_command_no_stdin_no_parameters(runner, httpserver, simple_user_payload):
    """No parameter nor stdin should display the help."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "create", "user"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Usage: cli create" in result.output


def test_command_validation_error(runner, httpserver, simple_user_payload):
    """Test pydantic errors handling."""
    httpserver.expect_request(
        "/Users",
        method="POST",
    ).respond_with_json(
        {"invalid": "json"},
        status=201,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "create",
            "user",
            "--user-name",
            "new-user@example.com",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Expected type User but got undefined object with no schema" in result.output
