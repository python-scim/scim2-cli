from typing import IO

import click
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.bulk import bulk_cli
from scim2_cli.create import create_cli
from scim2_cli.delete import delete_cli
from scim2_cli.modify import modify_cli
from scim2_cli.query import query_cli
from scim2_cli.replace import replace_cli
from scim2_cli.search import search_cli
from scim2_cli.session import Session
from scim2_cli.test import test_cli
from scim2_cli.utils import DOC_URL
from scim2_cli.utils import HeaderType
from scim2_cli.utils import split_headers


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
    ctx.obj = Session(
        url=url,
        headers=split_headers(header),
        verify=not no_verify,
        schemas=schemas,
        resource_types=resource_types,
        service_provider_config=service_provider_config,
    )


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
