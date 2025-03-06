import json
import re

import click
from httpx import Client
from scim2_client import SCIMClientError
from scim2_client.engines.httpx import SyncSCIMClient
from scim2_models import Group
from scim2_models import ListResponse
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ServiceProviderConfig
from scim2_models import User
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.create import create_cli
from scim2_cli.delete import delete_cli
from scim2_cli.query import query_cli
from scim2_cli.replace import replace_cli
from scim2_cli.search import search_cli
from scim2_cli.test import test_cli
from scim2_cli.utils import DOC_URL
from scim2_cli.utils import HeaderType
from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import split_headers


def load_config_files(
    schemas_fd, resource_types_fd, service_provider_config_fd
) -> tuple[
    list[type[Resource]], list[ResourceType] | None, ServiceProviderConfig | None
]:
    if schemas_fd:
        schemas_payload = json.load(schemas_fd)
        if isinstance(schemas_payload, dict):
            schemas_obj = ListResponse[Schema].model_validate(schemas_payload).resources
        else:
            schemas_obj = [Schema.model_validate(schema) for schema in schemas_payload]
        resource_models = [Resource.from_schema(schema) for schema in schemas_obj]

    else:
        resource_models = [User, Group]

    if resource_types_fd:
        resource_types_payload = json.load(resource_types_fd)
        if isinstance(schemas_payload, dict):
            resource_types = (
                ListResponse[ResourceType]
                .model_validate(resource_types_payload)
                .resources
            )
        else:
            resource_types = [
                ResourceType.model_validate(item) for item in resource_types_payload
            ]
    else:
        resource_types = None

    if service_provider_config_fd:
        spc_payload = json.load(service_provider_config_fd)
        service_provider_config = ServiceProviderConfig.model_validate(spc_payload)
    else:
        service_provider_config = None

    return resource_models, resource_types, service_provider_config


@click.group(cls=make_rst_to_ansi_formatter(DOC_URL, group=True))
@click.option("-u", "--url", help="The SCIM server endpoint.", envvar="SCIM_CLI_URL")
@click.option(
    "-h",
    "--header",
    multiple=True,
    type=HeaderType(),
    help="Headers to pass in the HTTP requests. Can be passed multiple times.",
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

    resource_models, resource_types_obj, spc_obj = load_config_files(
        schemas, resource_types, service_provider_config
    )

    scim_client = SyncSCIMClient(
        client,
        resource_models=resource_models,
        resource_types=resource_types_obj,
        service_provider_config=spc_obj,
    )
    try:
        scim_client.discover(
            schemas=not bool(schemas),
            resource_types=not bool(resource_types),
            service_provider_config=not bool(service_provider_config),
        )
    except SCIMClientError as exc:
        raise exception_to_click_error(exc) from exc

    ctx.obj["client"] = scim_client
    ctx.obj["resource_models"] = {
        re.sub(r"\[.*\]", "", resource_model.__name__.lower()): resource_model
        for resource_model in ctx.obj["client"].resource_models
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
