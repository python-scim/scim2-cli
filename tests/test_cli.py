import json
import os

import click
import pytest
from scim2_models import AuthenticationScheme
from scim2_models import Bulk
from scim2_models import ChangePassword
from scim2_models import Error
from scim2_models import ETag
from scim2_models import Filter
from scim2_models import ListResponse
from scim2_models import Patch
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ServiceProviderConfig
from scim2_models import Sort
from scim2_models import User

from scim2_cli import cli
from scim2_cli.create import create_cli
from scim2_cli.replace import replace_cli


def test_no_url(runner):
    result = runner.invoke(cli, ["create"])
    assert result.exit_code == 1
    assert "No SCIM server URL defined.\n" in result.output


def test_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SCIM application development CLI.\n" in result.output


def test_bad_server(runner):
    """Test that the discovery step display a readable error when a bad server has been passed."""
    result = runner.invoke(cli, ["--url", "http://scim.invalid", "query"])
    assert result.exit_code == 1
    assert "Error: Network error happened during request\n" in result.output


def test_stdin_bad_json(runner, httpserver):
    """Test that invalid JSON stdin raise an error."""
    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "query", "user"],
        input="invalid",
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "Invalid JSON input." in result.output


def test_auth_headers(runner, httpserver, simple_user_payload):
    """Test passing auth bearer headers."""
    httpserver.expect_request(
        "/Users/foobar",
        method="GET",
        headers={"Authorization": "Bearer token", "foo": "bar"},
    ).respond_with_json(
        simple_user_payload("foobar"),
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "query",
            "user",
            "foobar",
        ],
    )
    assert result.exit_code == 1

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "--header",
            "Authorization: Bearer token",
            "--header",
            "foo: bar",
            "query",
            "user",
            "foobar",
        ],
    )
    assert result.exit_code == 0


def test_env_vars(runner, httpserver, simple_user_payload):
    """Test passing host and headers with environment vars."""
    httpserver.expect_request(
        "/Users/foobar",
        method="GET",
        headers={"Authorization": "Bearer token", "foo": "bar"},
    ).respond_with_json(
        simple_user_payload("foobar"),
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(cli, ["query", "user"])
    assert result.exit_code == 1

    os.environ["SCIM_CLI_URL"] = httpserver.url_for("/")
    os.environ["SCIM_CLI_HEADERS"] = "Authorization: Bearer token;foo: bar"
    try:
        result = runner.invoke(cli, ["query", "user", "foobar"], catch_exceptions=False)
        assert result.exit_code == 0
    finally:
        del os.environ["SCIM_CLI_URL"]
        del os.environ["SCIM_CLI_HEADERS"]


@pytest.fixture
def service_provider_configuration():
    return ServiceProviderConfig(
        documentation_uri="https://scim.test",
        patch=Patch(supported=False),
        bulk=Bulk(supported=False, max_operations=0, max_payload_size=0),
        change_password=ChangePassword(supported=True),
        filter=Filter(supported=False, max_results=0),
        sort=Sort(supported=False),
        etag=ETag(supported=False),
        authentication_schemes=[
            AuthenticationScheme(
                name="OAuth Bearer Token",
                description="Authentication scheme using the OAuth Bearer Token Standard",
                spec_uri="http://www.rfc-editor.org/info/rfc6750",
                documentation_uri="https://scim.test",
                type="oauthbearertoken",
                primary=True,
            ),
        ],
    )


@pytest.fixture
def schemas():
    return [User.to_schema()]


@pytest.fixture
def resource_types():
    return [
        ResourceType(
            id="User",
            name="User",
            endpoint="/somewhere-different",
            description="User accounts",
            schema_="urn:ietf:params:scim:schemas:core:2.0:User",
        )
    ]


def test_custom_configuration_by_parameter(
    runner,
    httpserver,
    simple_user_payload,
    tmp_path,
    service_provider_configuration,
    schemas,
    resource_types,
):
    """Test passing custom .JSON configuration files to the command."""
    spc_path = tmp_path / "service_provider_configuration.json"
    with open(spc_path, "w") as fd:
        json.dump(service_provider_configuration.model_dump(), fd)

    schemas_path = tmp_path / "schemas.json"
    with open(schemas_path, "w") as fd:
        json.dump([schema.model_dump() for schema in schemas], fd)

    resource_types_path = tmp_path / "resource_types.json"
    with open(resource_types_path, "w") as fd:
        json.dump([resource_type.model_dump() for resource_type in resource_types], fd)

    httpserver.expect_request(
        "/somewhere-different/foobar",
        method="GET",
    ).respond_with_json(
        simple_user_payload("foobar"),
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "--service-provider-config",
            spc_path,
            "--schemas",
            schemas_path,
            "--resource-types",
            resource_types_path,
            "query",
            "user",
            "foobar",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0


def test_custom_configuration_in_list_response(
    runner,
    httpserver,
    simple_user_payload,
    tmp_path,
    service_provider_configuration,
    schemas,
    resource_types,
):
    """Test that ListResponse format is supported."""
    spc_path = tmp_path / "service_provider_configuration.json"
    with open(spc_path, "w") as fd:
        json.dump(service_provider_configuration.model_dump(), fd)

    schemas_path = tmp_path / "schemas.json"
    with open(schemas_path, "w") as fd:
        json.dump(
            ListResponse[Schema](
                total_results=len(schemas),
                start_index=1,
                items_per_page=len(schemas),
                resources=schemas,
            ).model_dump(),
            fd,
        )

    resource_types_path = tmp_path / "resource_types.json"
    with open(resource_types_path, "w") as fd:
        json.dump(
            ListResponse[ResourceType](
                total_results=len(resource_types),
                start_index=1,
                items_per_page=len(resource_types),
                resources=resource_types,
            ).model_dump(),
            fd,
        )

    httpserver.expect_request(
        "/somewhere-different/foobar",
        method="GET",
    ).respond_with_json(
        simple_user_payload("foobar"),
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "--service-provider-config",
            spc_path,
            "--schemas",
            schemas_path,
            "--resource-types",
            resource_types_path,
            "query",
            "user",
            "foobar",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0


@pytest.mark.parametrize("in_list_response", [False, True])
def test_custom_resource_types_only(
    runner, httpserver, simple_user_payload, tmp_path, resource_types, in_list_response
):
    """Test passing only the resource types, the schemas being discovered."""
    payload = (
        ListResponse[ResourceType](
            total_results=len(resource_types),
            start_index=1,
            items_per_page=len(resource_types),
            resources=resource_types,
        ).model_dump()
        if in_list_response
        else [resource_type.model_dump() for resource_type in resource_types]
    )
    resource_types_path = tmp_path / "resource_types.json"
    with open(resource_types_path, "w") as fd:
        json.dump(payload, fd)

    httpserver.expect_request(
        "/somewhere-different/foobar",
        method="GET",
    ).respond_with_json(
        simple_user_payload("foobar"),
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "--resource-types",
            resource_types_path,
            "query",
            "user",
            "foobar",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output


def test_custom_schemas_only(
    runner,
    httpserver,
    simple_user_payload,
    tmp_path,
    service_provider_configuration,
    schemas,
    resource_types,
):
    """Test passing only the schemas, the resource types being discovered."""
    schemas_path = tmp_path / "schemas.json"
    with open(schemas_path, "w") as fd:
        json.dump([schema.model_dump() for schema in schemas], fd)

    httpserver.clear_all_handlers()
    httpserver.expect_request("/ResourceTypes").respond_with_json(
        ListResponse[ResourceType](
            total_results=len(resource_types), resources=resource_types
        ).model_dump(),
        content_type="application/scim+json",
    )
    httpserver.expect_request("/ServiceProviderConfig").respond_with_json(
        service_provider_configuration.model_dump(),
        content_type="application/scim+json",
    )
    httpserver.expect_request(
        "/somewhere-different/foobar",
        method="GET",
    ).respond_with_json(
        simple_user_payload("foobar"),
        status=200,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "--schemas",
            schemas_path,
            "query",
            "user",
            "foobar",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output


def test_incoherent_server_description(runner, httpserver, tmp_path, schemas):
    """Test that a resource type naming an unknown schema displays a readable error."""
    resource_types_path = tmp_path / "resource_types.json"
    with open(resource_types_path, "w") as fd:
        json.dump(
            [
                ResourceType(
                    id="Group",
                    name="Group",
                    endpoint="/Groups",
                    schema_="urn:ietf:params:scim:schemas:core:2.0:Group",
                ).model_dump()
            ],
            fd,
        )

    result = runner.invoke(
        cli,
        [
            "--url",
            httpserver.url_for("/"),
            "--resource-types",
            resource_types_path,
            "query",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert (
        "Error: No resource describes urn:ietf:params:scim:schemas:core:2.0:Group"
        in result.output
    )


def test_custom_configuration_by_env(
    runner,
    httpserver,
    simple_user_payload,
    tmp_path,
    service_provider_configuration,
    schemas,
    resource_types,
):
    """Test passing custom .JSON configuration files to the command."""
    spc_path = tmp_path / "service_provider_configuration.json"
    with open(spc_path, "w") as fd:
        json.dump(service_provider_configuration.model_dump(), fd)

    schemas_path = tmp_path / "schemas.json"
    with open(schemas_path, "w") as fd:
        json.dump([schema.model_dump() for schema in schemas], fd)

    resource_types_path = tmp_path / "resource_types.json"
    with open(resource_types_path, "w") as fd:
        json.dump([resource_type.model_dump() for resource_type in resource_types], fd)

    httpserver.expect_request(
        "/somewhere-different/foobar",
        method="GET",
    ).respond_with_json(
        simple_user_payload("foobar"),
        status=200,
        content_type="application/scim+json",
    )

    os.environ["SCIM_CLI_SERVICE_PROVIDER_CONFIG"] = str(spc_path)
    os.environ["SCIM_CLI_SCHEMAS"] = str(schemas_path)
    os.environ["SCIM_CLI_RESOURCE_TYPES"] = str(resource_types_path)
    try:
        result = runner.invoke(
            cli,
            [
                "--url",
                httpserver.url_for("/"),
                "query",
                "user",
                "foobar",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
    finally:
        del os.environ["SCIM_CLI_SERVICE_PROVIDER_CONFIG"]
        del os.environ["SCIM_CLI_SCHEMAS"]
        del os.environ["SCIM_CLI_RESOURCE_TYPES"]


def test_discovery_scim_error(runner, httpserver):
    """Test that the discovery step displays a readable error when the server answers a SCIM error."""
    httpserver.clear_all_handlers()
    httpserver.expect_request("/ResourceTypes").respond_with_json(
        Error(status=403, detail="Insufficient permissions").model_dump(),
        status=403,
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli,
        ["--url", httpserver.url_for("/"), "query"],
        catch_exceptions=False,
    )
    assert result.exit_code == 1, result.output
    assert "Error: Insufficient permissions" in result.output


@pytest.mark.parametrize(
    "command", ["query", "search", "delete", "modify", "bulk", "test"]
)
@pytest.mark.parametrize(
    "url", [[], ["--url", "http://scim.invalid"]], ids=["no-url", "unreachable"]
)
def test_help_without_server(runner, command, url):
    """The help of the commands that do not depend on the server needs no server."""
    result = runner.invoke(cli, [*url, command, "--help"], env={"SCIM_CLI_URL": None})

    assert result.exit_code == 0, result.output
    assert f"Usage: cli {command}" in result.output


@pytest.mark.parametrize("command", ["create", "replace"])
def test_resource_type_subcommands_need_the_server(runner, command):
    """The resource type subcommands come from the server."""
    result = runner.invoke(cli, [command, "--help"], env={"SCIM_CLI_URL": None})

    assert result.exit_code == 1, result.output
    assert "No SCIM server URL defined." in result.output


@pytest.mark.parametrize("command", [create_cli, replace_cli])
def test_subcommands_without_server(command):
    """Without a server, as when the documentation is built, there are no subcommands."""
    assert command.list_commands(click.Context(command)) == []


def test_server_is_discovered_once(runner, httpserver, simple_user_payload):
    """The server is discovered once per command."""
    httpserver.expect_request("/Users/1").respond_with_json(
        simple_user_payload("1"), content_type="application/scim+json"
    )

    result = runner.invoke(
        cli, ["--url", httpserver.url_for("/"), "query", "user", "1"]
    )

    assert result.exit_code == 0, result.output
    discoveries = [
        request.path
        for request, _ in httpserver.log
        if request.path in ("/ResourceTypes", "/Schemas", "/ServiceProviderConfig")
    ]
    assert sorted(discoveries) == [
        "/ResourceTypes",
        "/Schemas",
        "/ServiceProviderConfig",
    ]
