import click
from click import ClickException
from scim2_models import Message
from scim2_models import Resource
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.utils import exception_to_click_error

from .utils import DOC_URL
from .utils import SCIM_EXCEPTIONS
from .utils import formatted_payload


@click.command(cls=make_rst_to_ansi_formatter(DOC_URL), name="delete")
@click.argument("resource-type", required=True)
@click.argument("id", required=True)
@click.option(
    "--indent/--no-indent",
    is_flag=True,
    default=True,
    help="Indent JSON response payloads.",
)
@click.pass_context
def delete_cli(ctx, resource_type, id, indent):
    """Perform a `SCIM DELETE query <https://www.rfc-editor.org/rfc/rfc7644#section-3.6>`_ request.

    .. code-block:: bash

         delete user 1234
    """
    try:
        resource_model = ctx.obj["resource_models"][resource_type]
    except KeyError as exc:
        ok_values = ", ".join(ctx.obj["resource_models"])
        raise ClickException(
            f"Unknown resource type '{resource_type}'. Available values are: {ok_values}'"
        ) from exc

    try:
        response = ctx.obj["client"].delete(resource_model, id, raise_scim_errors=False)

    except SCIM_EXCEPTIONS as scim_exc:
        raise exception_to_click_error(scim_exc) from scim_exc

    if response:
        payload = (
            response.model_dump()
            if isinstance(response, Resource | Message)
            else response
        )
        payload = formatted_payload(payload, indent)
        click.echo(payload)
