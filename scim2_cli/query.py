from typing import Any

import click
from click import ClickException
from scim2_client import Me
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import ResponseParameters
from scim2_models import Schema
from scim2_models import SearchRequest
from scim2_models import ServiceProviderConfig
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from scim2_cli.utils import exception_to_click_error
from scim2_cli.utils import find_target
from scim2_cli.utils import me_option

from .utils import DOC_URL
from .utils import SCIM_EXCEPTIONS
from .utils import formatted_payload

DISCOVERY_MODELS = (Schema, ResourceType, ServiceProviderConfig)


@click.command(cls=make_rst_to_ansi_formatter(DOC_URL), name="query")
@click.pass_context
@click.argument("resource_type", required=False)
@click.argument("id", required=False)
@click.option(
    "--attribute",
    multiple=True,
    help="A multi-valued list of strings indicating the names of resource attributes to return in the response, overriding the set of attributes that would be returned by default.",
)
@click.option(
    "--excluded-attribute",
    multiple=True,
    help="A multi-valued list of strings indicating the names of resource attributes to be removed from the default set of attributes to return.",
)
@click.option(
    "--start-index",
    type=int,
    help="An integer indicating the 1-based index of the first query result.",
)
@click.option(
    "--cursor",
    help="The cursor of the page to read, for cursor-based pagination (RFC 9865). Pass an empty value to read the first page.",
)
@click.option(
    "--count",
    type=int,
    help="An integer indicating the desired maximum number of query results per page.",
)
@click.option(
    "--filter", help="The filter string used to request a subset of resources."
)
@click.option(
    "--sort-by",
    help="A string indicating the attribute whose value SHALL be used to order the returned responses.",
)
@click.option(
    "--sort-order",
    help="A string indicating the order in which the “sortBy” parameter is applied.",
)
@me_option()
@click.option(
    "--indent/--no-indent",
    is_flag=True,
    default=True,
    help="Indent JSON response payloads.",
)
def query_cli(
    ctx: click.Context,
    resource_type: str | None,
    id: str | None,
    attribute: list[str],
    excluded_attribute: list[str],
    start_index: int | None,
    cursor: str | None,
    count: int | None,
    filter: str | None,
    sort_by: str | None,
    sort_order: str | None,
    me: bool,
    indent: bool,
) -> None:
    """Perform a `SCIM GET <https://www.rfc-editor.org/rfc/rfc7644#section-3.4.1>`_ request on the :code:`RESOURCE_TYPE` endpoint.

    - If :code:`RESOURCE_TYPE` is :code:`user` and :code:`id` is `1234`, then the request will made on the :code:`/Users/1234` endpoint.
    - If :code:`RESOURCE_TYPE` is :code:`user` and :code:`id` is not set, then the request will made on the :code:`/Users` endpoint.
    - If :code:`RESOURCE_TYPE` is not set, then the request will made on the :code:`/` endpoint.
    - If :code:`--me` is set, then the request will be made on the :code:`/Me` endpoint.

    When a single resource is queried, only :code:`--attribute` and :code:`--excluded-attribute` are
    available, as defined in `RFC7644 §3.4.1 <https://www.rfc-editor.org/rfc/rfc7644#section-3.4.1>`_.

    Data passed in JSON format to stdin is sent as request arguments and all the other query arguments are ignored:

    .. code-block:: bash

        echo '{"startIndex": 50, "count": 10}' |  query user

    """
    if me and (resource_type or id):
        raise ClickException("--me cannot be used with a resource type or an id.")

    target: ResourceType | type[Resource[Any]] | None = None
    if resource_type:
        targets: dict[str, ResourceType | type[Resource[Any]]] = {
            **ctx.obj.resource_types,
            **{model.__name__.lower(): model for model in DISCOVERY_MODELS},
        }
        target = find_target(targets, resource_type)

    single_resource = me or bool(id) or target is ServiceProviderConfig
    listing_options = [
        name
        for name, value in (
            ("--start-index", start_index),
            ("--cursor", cursor),
            ("--count", count),
            ("--filter", filter),
            ("--sort-by", sort_by),
            ("--sort-order", sort_order),
        )
        if value is not None
    ]
    if single_resource and listing_options:
        raise ClickException(
            f"{', '.join(listing_options)} cannot be used when querying a single resource."
        )

    if ctx.obj.stdin:
        check_request_payload = False
        payload = ctx.obj.stdin

    elif single_resource:
        check_request_payload = True
        payload = ResponseParameters.model_validate(
            {
                "attributes": attribute or None,
                "excluded_attributes": excluded_attribute or None,
            }
        )

    else:
        check_request_payload = True
        payload = SearchRequest.model_validate(
            {
                "attributes": attribute or None,
                "excluded_attributes": excluded_attribute or None,
                "start_index": start_index,
                "cursor": cursor,
                "count": count,
                "filter": filter,
                "sort_by": sort_by,
                "sort_order": sort_order,
            }
        )

    try:
        response = ctx.obj.client.query(
            Me if me else target,
            id,
            query_parameters=payload,
            check_request_payload=check_request_payload,
            raise_scim_errors=False,
        )

    except SCIM_EXCEPTIONS as scim_exc:
        raise exception_to_click_error(scim_exc) from scim_exc

    payload = formatted_payload(response.model_dump(), indent)
    click.echo(payload)
