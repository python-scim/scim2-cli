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

from scim2_cli.utils import DOC_URL
from scim2_cli.utils import SCIM_EXCEPTIONS
from scim2_cli.utils import ModelCommand
from scim2_cli.utils import command_name
from scim2_cli.utils import escape_options_help
from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import formatted_payload
from scim2_cli.utils import me_option
from scim2_cli.utils import unacceptable_fields


def create_payload(
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
            client.create(
                Me if me else resource_type, payload, raise_scim_errors=False
            ),
        )

    except SCIM_EXCEPTIONS as scim_exc:
        raise exception_to_click_error(scim_exc) from scim_exc

    click.echo(formatted_payload(response.model_dump(), indent))


def create_factory(
    resource_type: ResourceType, model: type[Resource[Any]]
) -> click.Command:
    exclude = unacceptable_fields(Context.RESOURCE_CREATION_REQUEST, model)

    @click.command(
        cls=make_rst_to_ansi_formatter(DOC_URL),
        name=command_name(resource_type),
    )
    @click.option(
        "--indent/--no-indent",
        is_flag=True,
        default=True,
        help="Indent JSON response payloads.",
    )
    @me_option
    @from_pydantic("obj", model, exclude=exclude)
    @click.pass_context
    def create_command(
        ctx: click.Context,
        indent: bool,
        me: bool,
        obj: Resource[Any] | None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        r"""Perform a `SCIM POST <https://www.rfc-editor.org/rfc/rfc7644#section-3.3>`_ request on resources endpoint.

        Input data can be passed through parameters like :code:`--external-id`.

        .. code-block:: bash

            scim create user --user-name "foo" --name-given-name "bar"

        Multiple attributes should be passed as JSON payloads:

        .. code-block:: bash

            scim create user \\
                --user-name "foo" \\
                --emails '[{"value":"foo@bar.example", "primary": true}, {"value": "foo@baz.example"}]'

        Input can also be passed through stdin in JSON format:

        .. code-block:: bash

            echo '{"userName": "bjensen@example.com", "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]}' |  create user

        With :code:`--me`, the request is made on the :code:`/Me` endpoint,
        and the server chooses the resource type:

        .. code-block:: bash

            scim create user --me --user-name "foo"

        """
        if obj == model():
            obj = None

        payload = ctx.obj.get("stdin") or obj
        if not payload:
            click.echo(ctx.get_help())
            ctx.exit(1)

        create_payload(
            ctx.obj["client"],
            resource_type,
            payload,
            indent,
            me or ctx.obj.get("me", False),
        )

    return escape_options_help(create_command)


@click.command(
    cls=ModelCommand,
    factory=create_factory,
    name="create",
    invoke_without_command=True,
)
@click.pass_context
@click.option(
    "--indent/--no-indent",
    is_flag=True,
    default=True,
    help="Indent JSON response payloads.",
)
@me_option
def create_cli(ctx: click.Context, indent: bool, me: bool) -> None:
    """Perform a `SCIM POST <https://www.rfc-editor.org/rfc/rfc7644#section-3.3>`_ request on resources endpoint.

    There are subcommands for all the resource types of the server, with dynamic attributes.
    See the attributes for :code:`user` with:

    .. code-block:: bash

         create user --help

    If no subcommand is executed, input data is expected to be passed in JSON format to stdin:

    .. code-block:: bash

        echo '{"userName": "bjensen@example.com", "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]}' |  create

    With :code:`--me`, the request is made on the :code:`/Me` endpoint,
    and the server chooses the resource type.

    """
    if ctx.invoked_subcommand is not None:
        ctx.obj["me"] = me
        return

    payload = ctx.obj.get("stdin")
    if not payload:
        click.echo(ctx.get_help())
        ctx.exit(1)

    create_payload(ctx.obj["client"], None, payload, indent, me)
