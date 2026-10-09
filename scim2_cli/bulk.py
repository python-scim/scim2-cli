import click
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.utils import DOC_URL
from scim2_cli.utils import SCIM_EXCEPTIONS
from scim2_cli.utils import echo_response
from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import indent_option


@click.command(cls=make_rst_to_ansi_formatter(DOC_URL), name="bulk")
@indent_option()
@click.pass_context
def bulk_cli(ctx: click.Context, indent: bool) -> None:
    """Perform a `SCIM bulk <https://www.rfc-editor.org/rfc/rfc7644#section-3.7>`_ request.

    The bulk request is passed through stdin in JSON format:

    .. code-block:: bash

        echo '{"schemas": ["urn:ietf:params:scim:api:messages:2.0:BulkRequest"], "Operations": [{"method": "POST", "path": "/Users", "bulkId": "qwerty", "data": {"schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"], "userName": "bjensen@example.com"}}]}' |  bulk

    The request is checked against the bulk capabilities of the server before being sent.
    """
    payload = ctx.obj.stdin
    if not payload:
        click.echo(ctx.get_help())
        ctx.exit(1)

    try:
        response = ctx.obj.client.bulk(payload, raise_scim_errors=False)

    except SCIM_EXCEPTIONS as scim_exc:
        raise exception_to_click_error(scim_exc) from scim_exc

    echo_response(response, indent)
