import json
import re
from collections.abc import Callable
from enum import StrEnum
from typing import TYPE_CHECKING
from typing import Any

import click
from scim2_client import SCIMClientException
from scim2_models import BaseModel
from scim2_models import Context
from scim2_models import Mutability
from scim2_models import Resource
from scim2_models import SCIMException
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

DOC_URL = "https://scim2-cli.readthedocs.io/"
INDENTATION_SIZE = 4

SCIM_EXCEPTIONS = (SCIMClientException, SCIMException)

CONTROL_CHARACTERS = re.compile(
    "[\x00-\x08\x0b-\x1f\x7f-\x9f\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]"
)


class HeaderType(click.types.StringParamType):
    envvar_list_splitter = ";"
    name = "HEADER"


class Color(StrEnum):
    black = "black"
    red = "red"
    green = "green"
    yellow = "yellow"
    blue = "blue"
    magenta = "magenta"
    cyan = "cyan"
    white = "white"
    bright_black = "bright_black"
    bright_red = "bright_red"
    bright_green = "bright_green"
    bright_yellow = "bright_yellow"
    bright_blue = "bright_blue"
    bright_magenta = "bright_magenta"
    bright_cyan = "bright_cyan"
    bright_white = "bright_white"


def escape_control_characters(text: object) -> str:
    """Replace the control characters of a text by their escaped form.

    The texts coming from the server would otherwise be interpreted by the
    terminal as escape sequences.
    """
    return CONTROL_CHARACTERS.sub(
        lambda match: match.group().encode("unicode_escape").decode(), str(text)
    )


def escape_options_help(command: click.Command) -> click.Command:
    """Escape the option help texts pydanclick takes from the schema descriptions."""
    for param in command.params:
        if isinstance(param, click.Option) and param.help:
            param.help = escape_control_characters(param.help)
    return command


def formatted_payload(obj: Any, indent: bool) -> str:
    return json.dumps(obj, indent=INDENTATION_SIZE if indent else None)


def split_headers(headers: list[str]) -> dict[str, str]:
    """Make a dict from header strings.

    ['Authorization: Bearer token'] → '{"Authorization": "Bearer token"}'
    """
    return {
        header[: header.index(":")].strip(): header[header.index(":") + 1 :].strip()
        for header in headers
    }


# mypy cannot subclass a class built at runtime by a factory.
if TYPE_CHECKING:
    RSTCommand = click.Group
else:
    RSTCommand = make_rst_to_ansi_formatter(DOC_URL, group=True)


class ModelCommand(RSTCommand):
    """CLI commands that takes a model subcommand."""

    def __init__(
        self,
        *args: Any,
        factory: Callable[[type[Resource[Any]] | None], click.Command],
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.factory = factory

    def list_commands(self, ctx: click.Context) -> list[str]:
        ctx.ensure_object(dict)
        base = super().list_commands(ctx)
        lazy = sorted(ctx.obj.get("resource_models", {}).keys())
        return base + lazy

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command:
        model = ctx.obj["resource_models"].get(cmd_name)
        return self.factory(model)


def is_field_acceptable(
    context: Context, model: type[BaseModel], field_name: str
) -> bool:
    """Indicate whether a field is acceptable as part of a SCIM payload for a given context."""
    mutability = model.get_field_annotation(field_name, Mutability)

    if (
        context
        in (Context.RESOURCE_CREATION_REQUEST, Context.RESOURCE_REPLACEMENT_REQUEST)
        and mutability == Mutability.read_only
    ):
        return False

    if (
        context in (Context.RESOURCE_QUERY_REQUEST, Context.SEARCH_REQUEST)
        and mutability == Mutability.write_only
    ):
        return False

    if (
        context == Context.RESOURCE_REPLACEMENT_REQUEST
        and mutability == Mutability.immutable
    ):
        return False

    return True


def unacceptable_fields(context: Context, model: type[BaseModel]) -> list[str]:
    excluded = [
        field_name
        for field_name in model.model_fields
        if not is_field_acceptable(context, model, field_name)
    ]
    excluded.append("schemas")
    return excluded


def exception_to_click_error(exception: Exception) -> click.ClickException:
    message = str(exception)
    if hasattr(exception, "__notes__"):
        message += "\n" + "\n".join(exception.__notes__)
    return click.ClickException(escape_control_characters(message))
