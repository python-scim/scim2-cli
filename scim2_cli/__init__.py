import json
import sys
from typing import IO
from typing import Any
from typing import TypeVar
from typing import cast

import click
from httpx2 import Client
from scim2_client.engines.httpx2 import SyncSCIMClient
from scim2_models import ListResponse
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ScimProvider
from scim2_models import ScimProviderError
from scim2_models import ServiceProviderConfig
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.bulk import bulk_cli
from scim2_cli.create import create_cli
from scim2_cli.delete import delete_cli
from scim2_cli.modify import modify_cli
from scim2_cli.query import query_cli
from scim2_cli.replace import replace_cli
from scim2_cli.search import search_cli
from scim2_cli.test import test_cli
from scim2_cli.utils import DOC_URL
from scim2_cli.utils import SCIM_EXCEPTIONS
from scim2_cli.utils import HeaderType
from scim2_cli.utils import command_name
from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import split_headers

ResourceT = TypeVar("ResourceT", bound=Resource[Any])


def load_objects(fd: IO[str], model: type[ResourceT]) -> list[ResourceT]:
    """Read a list of objects, bare or wrapped in a ListResponse, from a JSON file."""
    payload = json.load(fd)
    if isinstance(payload, dict):
        list_response: ListResponse[ResourceT] = cast(Any, ListResponse)[
            model
        ].model_validate(payload)
        return list_response.resources or []
    return [model.model_validate(item) for item in payload]


def describe_server(
    scim_client: SyncSCIMClient,
    schemas_fd: IO[str] | None,
    resource_types_fd: IO[str] | None,
    service_provider_config_fd: IO[str] | None,
) -> ScimProvider:
    """Describe the server with the configuration files, and query it for the others."""
    resource_types = (
        load_objects(resource_types_fd, ResourceType)
        if resource_types_fd
        else cast(
            "ListResponse[ResourceType]", scim_client.query(ResourceType)
        ).resources
        or []
    )
    schemas = (
        load_objects(schemas_fd, Schema)
        if schemas_fd
        else cast("ListResponse[Schema]", scim_client.query(Schema)).resources or []
    )
    config = (
        ServiceProviderConfig.model_validate(json.load(service_provider_config_fd))
        if service_provider_config_fd
        else cast(ServiceProviderConfig, scim_client.query(ServiceProviderConfig))
    )
    return ScimProvider.from_discovery(schemas, resource_types, config)


@click.group(cls=make_rst_to_ansi_formatter(DOC_URL, group=True))
@click.option("-u", "--url", help="The SCIM server endpoint.", envvar="SCIM_CLI_URL")
@click.option(
    "-h",
    "--header",
    multiple=True,
    type=HeaderType(),
    help="Headers to pass in the HTTP requests. Can be passed multiple times. Other users of the machine can see the command line arguments, so pass the secrets with the SCIM_CLI_HEADERS environment variable.",
    envvar="SCIM_CLI_HEADERS",
)
@click.option(
    "--no-verify",
    is_flag=True,
    default=False,
    help="Don't perform https certificate verifications.",
)
@click.option(
    "-s",
    "--schemas",
    type=click.File(),
    help="Path to a JSON file containing a list of SCIM Schemas. Those schemas will be assumed to be available on the server. If unset, they will be downloaded.",
    envvar="SCIM_CLI_SCHEMAS",
)
@click.option(
    "-r",
    "--resource-types",
    type=click.File(),
    help="Path to a JSON file containing a list of SCIM ResourceType. Those resource types will be assumed to be available on the server. If unset, they will be downloaded.",
    envvar="SCIM_CLI_RESOURCE_TYPES",
)
@click.option(
    "-c",
    "--service-provider-config",
    type=click.File(),
    help="Path to a JSON file containing the ServiceProviderConfig content of the server. Will be downloaded otherwise.",
    envvar="SCIM_CLI_SERVICE_PROVIDER_CONFIG",
)
@click.pass_context
def cli(
    ctx: click.Context,
    url: str | None,
    header: list[str],
    no_verify: bool,
    schemas: IO[str] | None,
    resource_types: IO[str] | None,
    service_provider_config: IO[str] | None,
) -> None:
    """SCIM application development CLI."""
    ctx.ensure_object(dict)

    if not url:
        raise click.ClickException("No SCIM server URL defined.")

    headers_dict = split_headers(header)
    client = Client(base_url=url, headers=headers_dict, verify=not no_verify)

    scim_client = SyncSCIMClient(client)
    try:
        scim_client.provider = describe_server(
            scim_client, schemas, resource_types, service_provider_config
        )
    except (*SCIM_EXCEPTIONS, ScimProviderError) as exc:
        raise exception_to_click_error(exc) from exc

    ctx.obj["client"] = scim_client
    ctx.obj["resource_types"] = {
        command_name(resource_type): resource_type
        for resource_type in scim_client.provider.resource_types
        if resource_type.name or resource_type.id
    }

    if not sys.stdin.isatty():  # pragma: no cover
        if stdin := sys.stdin.read().strip():
            try:
                ctx.obj["stdin"] = json.loads(stdin)
            except json.JSONDecodeError as exc:
                message = f"Invalid JSON input.\n{exc}"
                raise click.ClickException(message) from exc


cli.add_command(create_cli)
cli.add_command(query_cli)
cli.add_command(replace_cli)
cli.add_command(modify_cli)
cli.add_command(delete_cli)
cli.add_command(search_cli)
cli.add_command(bulk_cli)
cli.add_command(test_cli)

if __name__ == "__main__":  # pragma: no cover
    cli()
