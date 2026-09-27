import json
import re

import click
from httpx2 import Client
from scim2_client.engines.httpx2 import SyncSCIMClient
from scim2_models import ListResponse
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ScimProvider
from scim2_models import ScimProviderError
from scim2_models import ServiceProviderConfig
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.create import create_cli
from scim2_cli.delete import delete_cli
from scim2_cli.query import query_cli
from scim2_cli.replace import replace_cli
from scim2_cli.search import search_cli
from scim2_cli.test import test_cli
from scim2_cli.utils import DOC_URL
from scim2_cli.utils import SCIM_EXCEPTIONS
from scim2_cli.utils import HeaderType
from scim2_cli.utils import escape_control_characters
from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import split_headers


def load_objects(fd, model):
    """Read a list of objects, bare or wrapped in a ListResponse, from a JSON file."""
    payload = json.load(fd)
    if isinstance(payload, dict):
        return ListResponse[model].model_validate(payload).resources or []
    return [model.model_validate(item) for item in payload]


def describe_server(
    scim_client, schemas_fd, resource_types_fd, service_provider_config_fd
) -> ScimProvider:
    """Describe the server with the configuration files, and query it for the others."""
    resource_types = (
        load_objects(resource_types_fd, ResourceType)
        if resource_types_fd
        else scim_client.query(ResourceType).resources or []
    )
    schemas = (
        load_objects(schemas_fd, Schema)
        if schemas_fd
        else scim_client.query(Schema).resources or []
    )
    config = (
        ServiceProviderConfig.model_validate(json.load(service_provider_config_fd))
        if service_provider_config_fd
        else scim_client.query(ServiceProviderConfig)
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
    ctx,
    url: str,
    header: list[str],
    no_verify,
    schemas,
    resource_types,
    service_provider_config,
):
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

    provider = scim_client.provider
    ctx.obj["client"] = scim_client
    ctx.obj["resource_models"] = {
        escape_control_characters(
            re.sub(r"\[.*\]", "", resource_model.__name__.lower())
        ): resource_model
        for resource_model in map(provider.model_for, provider.resource_types)
    }

    if not click.get_text_stream("stdin").isatty():  # pragma: no cover
        if stdin := click.get_text_stream("stdin").read().strip():
            try:
                ctx.obj["stdin"] = json.loads(stdin)
            except json.JSONDecodeError as exc:
                message = f"Invalid JSON input.\n{exc}"
                raise click.ClickException(message) from exc


cli.add_command(create_cli)
cli.add_command(query_cli)
cli.add_command(replace_cli)
cli.add_command(delete_cli)
cli.add_command(search_cli)
cli.add_command(test_cli)

if __name__ == "__main__":  # pragma: no cover
    cli()
