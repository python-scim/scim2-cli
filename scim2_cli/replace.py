from typing import Any
from typing import cast

import click
from pydanclick import from_pydantic
from scim2_client import Me
from scim2_client.engines.httpx2 import SyncSCIMClient
from scim2_models import Context
from scim2_models import Error
from scim2_models import Resource
from scim2_models import ResourceType
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.utils import command_name
from scim2_cli.utils import escape_options_help
from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import indent_option
from scim2_cli.utils import inherited
from scim2_cli.utils import me_option

from .utils import DOC_URL
from .utils import SCIM_EXCEPTIONS
from .utils import ModelCommand
from .utils import formatted_payload
from .utils import renamed_fields
from .utils import unacceptable_fields


def replace_payload(
    client: SyncSCIMClient,
    resource_type: ResourceType | None,
    payload: Resource[Any] | dict[str, Any],
    indent: bool,
    me: bool,
) -> None:
    try:
        # Response payloads are always checked, so the client never returns a dict.
        response = cast(
            "Resource[Any] | Error",
            client.replace(
                Me if me else resource_type, payload, raise_scim_errors=False
            ),
        )

    except SCIM_EXCEPTIONS as scim_exc:
        raise exception_to_click_error(scim_exc) from scim_exc

    click.echo(formatted_payload(response.model_dump(), indent))


def replace_factory(
    resource_type: ResourceType, model: type[Resource[Any]]
) -> click.Command:
    exclude = unacceptable_fields(Context.RESOURCE_REPLACEMENT_REQUEST, model)
    exclude.remove("id")

    @click.command(
        cls=make_rst_to_ansi_formatter(DOC_URL),
        name=command_name(resource_type),
    )
    @indent_option("cli_indent")
    @me_option("cli_me")
    @from_pydantic("obj", model, exclude=exclude, rename=renamed_fields(model, exclude))
    @click.pass_context
    def replace_command(
        ctx: click.Context,
        cli_indent: bool,
        cli_me: bool,
        obj: Resource[Any] | None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        r"""Perform a `SCIM PUT <https://www.rfc-editor.org/rfc/rfc7644#section-3.3>`_ request on resources endpoint.

        Input data can be passed through parameters like :code:`--external-id`.

        .. code-block:: bash

             replace user --id "xxxx-yyyy" --user-name "foo" --name-given-name "bar"

        Multiple attributes should be passed as JSON payloads:

        .. code-block:: bash

             replace user \
                --id "xxxx-yyyy" \
                --user-name "foo" \
                --emails '[{"value":"foo@bar.example", "primary": true}, {"value": "foo@baz.example"}]'

        Input can also be passed through stdin in JSON format:

        .. code-block:: bash

            echo '{"id": "xxxx-yyyy", "userName": "bjensen@example.com", "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]}' |  replace user

        With :code:`--me`, the request is made on the :code:`/Me` endpoint,
        and :code:`--id` is not needed:

        .. code-block:: bash

            scim replace user --me --user-name "foo"

        """
        if obj == model():
            obj = None

        payload = ctx.obj.stdin or obj
        if not payload:
            click.echo(ctx.get_help())
            ctx.exit(1)

        replace_payload(
            ctx.obj.client,
            resource_type,
            payload,
            inherited(ctx, "cli_indent", cli_indent),
            inherited(ctx, "cli_me", cli_me),
        )

    return escape_options_help(replace_command)


@click.command(
    cls=ModelCommand,
    factory=replace_factory,
    name="replace",
    invoke_without_command=True,
)
@click.pass_context
@indent_option("cli_indent")
@me_option("cli_me")
def replace_cli(ctx: click.Context, cli_indent: bool, cli_me: bool) -> None:
    """Perform a `SCIM PUT <https://www.rfc-editor.org/rfc/rfc7644#section-3.5.1>`_ request on the resources endpoint.

    There are subcommands for all the resource types of the server, with dynamic attributes.
    See the attributes for :code:`user` with:

    .. code-block:: bash

         replace user --help

    If no subcommand is executed, input data is expected to be passed in JSON format to stdin:

    .. code-block:: bash

        echo '{"userName": "bjensen@example.com", "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"], "id": "1234"}' |  replace user

    With :code:`--me`, the request is made on the :code:`/Me` endpoint,
    and the id is not needed.

    """
    if ctx.invoked_subcommand is not None:
        return

    payload = ctx.obj.stdin
    if not payload:
        click.echo(ctx.get_help())
        ctx.exit(1)

    replace_payload(ctx.obj.client, None, payload, cli_indent, cli_me)
