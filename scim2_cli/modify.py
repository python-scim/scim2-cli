import json
from decimal import Decimal
from typing import Any

import click
from click import ClickException
from pydantic import ValidationError
from scim2_client import Me
from scim2_models import BaseModel
from scim2_models import Context
from scim2_models import Error
from scim2_models import InvalidPathException
from scim2_models import PatchOp
from scim2_models import Path
from scim2_models import Resource
from scim2_models import SCIMException
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.utils import DOC_URL
from scim2_cli.utils import SCIM_EXCEPTIONS
from scim2_cli.utils import escape_control_characters
from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import find_target
from scim2_cli.utils import formatted_payload
from scim2_cli.utils import indent_option
from scim2_cli.utils import me_option

OPERATIONS = {"add": 2, "replace": 2, "remove": 1}
JSON_TYPES = (bool, int, float, Decimal, BaseModel)


def parse_operations(tokens: tuple[str, ...]) -> list[tuple[str, str, str | None]]:
    """Split the arguments into operations, each one followed by its path and its value."""
    operations: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(tokens):
        op = tokens[index].lower()
        if op not in OPERATIONS:
            raise ClickException(
                f"Unknown operation '{escape_control_characters(tokens[index])}'. "
                f"Available values are: {', '.join(OPERATIONS)}"
            )

        nargs = OPERATIONS[op]
        arguments = tokens[index + 1 : index + 1 + nargs]
        if len(arguments) < nargs or (op == "remove" and not arguments[0]):
            expected = "a path and a value" if nargs == 2 else "a path"
            raise ClickException(f"The '{op}' operation takes {expected}.")

        path, *value = arguments
        operations.append((op, path, value[0] if value else None))
        index += 1 + nargs

    return operations


def serves(model: type[Resource[Any]], path: str) -> bool:
    """Tell whether a path designates an attribute or an extension of a model."""
    bound = Path[model](path)  # type: ignore[valid-type]
    return bound.resolve() is not None or bound.model is not None


def is_json(model: type[Resource[Any]], path: str) -> bool:
    """Tell whether the value of an attribute is written in JSON rather than as a plain string."""
    bound = Path[model](path)  # type: ignore[valid-type]
    binding = bound.resolve()
    if binding is None:
        return True

    if binding.is_multivalued and not binding.sub_field_name and not bound.value_filter:
        return True

    target = binding.target_type
    return isinstance(target, type) and issubclass(target, JSON_TYPES)


def read_value(model: type[Resource[Any]], path: str, value: str) -> Any:
    """Read a value with the type of the attribute it is meant for."""
    if not is_json(model, path):
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ClickException(
            f"Invalid JSON value for '{escape_control_characters(path)}': {exc}"
        ) from exc


def build_patch(
    models: list[type[Resource[Any]]], operations: list[tuple[str, str, str | None]]
) -> PatchOp[Resource[Any]]:
    """Build the patch operation of the first model that has all the attributes."""
    paths = [path for _, path, _ in operations]
    for path in paths:
        try:
            Path(path)
        except InvalidPathException as exc:
            raise ClickException(
                f"Invalid path '{escape_control_characters(path)}': {exc}"
            ) from exc

    model = next(
        (model for model in models if all(serves(model, path) for path in paths)),
        None,
    )
    if model is None:
        unknown = [
            path for path in paths if not any(serves(model, path) for model in models)
        ]
        message = (
            "Unknown attributes: "
            if unknown
            else "No resource type has all the attributes: "
        )
        raise ClickException(
            message
            + ", ".join(escape_control_characters(path) for path in unknown or paths)
        )

    patch_operations = []
    for op, path, value in operations:
        operation = {"op": op}
        if path:
            operation["path"] = path
        if value is not None:
            operation["value"] = read_value(model, path, value)
        patch_operations.append(operation)

    try:
        return PatchOp[model].model_validate({"Operations": patch_operations})  # type: ignore[valid-type]
    except ValidationError as exc:
        error = Error.from_validation_errors(exc)[0]
        raise exception_to_click_error(
            SCIMException.from_error(error, scim_ctx=Context.RESOURCE_PATCH_REQUEST)
        ) from exc


@click.command(cls=make_rst_to_ansi_formatter(DOC_URL), name="modify")
@click.argument("arguments", nargs=-1, metavar="[RESOURCE_TYPE ID] OPERATION...")
@me_option()
@indent_option()
@click.pass_context
def modify_cli(
    ctx: click.Context, arguments: tuple[str, ...], me: bool, indent: bool
) -> None:
    r"""Perform a `SCIM PATCH <https://www.rfc-editor.org/rfc/rfc7644#section-3.5.2>`_ request.

    The operations follow the resource type and the id. They are applied in order:

    - :code:`add PATH VALUE` adds a value,
    - :code:`replace PATH VALUE` replaces a value,
    - :code:`remove PATH` removes a value.

    .. code-block:: bash

        modify user 1234 replace displayName "Barbara Jensen" \
            remove 'emails[type eq "work"]' \
            add emails '[{"value": "bjensen@example.com", "type": "work"}]'

    Values of string attributes are passed as is, the other values are passed in JSON.
    An empty path applies a JSON object of attributes to the resource.
    Pass :code:`--` before the operations if a value starts with :code:`-`.

    With :code:`--me`, the request is made on the :code:`/Me` endpoint:

    .. code-block:: bash

        modify --me replace displayName "Barbara Jensen"

    A patch operation can also be passed through stdin in JSON format:

    .. code-block:: bash

        echo '{"schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"], "Operations": [{"op": "replace", "value": {"displayName": "Barbara Jensen"}}]}' |  modify user 1234

    """
    resource_types = ctx.obj.resource_types
    provider = ctx.obj.client.provider
    if me and arguments and arguments[0].lower() in resource_types:
        raise ClickException("--me cannot be used with a resource type or an id.")

    if me:
        target, id, tokens = Me, None, arguments
        models = list(
            dict.fromkeys(provider.model_for(rt) for rt in resource_types.values())
        )
    elif len(arguments) < 2:
        raise ClickException("Pass a resource type and an id, or --me.")
    else:
        target = find_target(resource_types, arguments[0])
        id, tokens = arguments[1], arguments[2:]
        models = [provider.model_for(target)]

    stdin = ctx.obj.stdin
    if stdin and tokens:
        raise ClickException("Pass the operations either as arguments or to stdin.")

    if not stdin and not tokens:
        raise ClickException("Missing operation.")

    payload = stdin or build_patch(models, parse_operations(tokens))
    try:
        response = ctx.obj.client.modify(target, id, payload, raise_scim_errors=False)

    except SCIM_EXCEPTIONS as scim_exc:
        raise exception_to_click_error(scim_exc) from scim_exc

    if response is not None:
        click.echo(formatted_payload(response.model_dump(), indent))
