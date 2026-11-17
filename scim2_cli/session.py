import json
import sys
from collections.abc import Callable
from functools import cached_property
from functools import partial
from typing import IO
from typing import Any
from typing import TypeVar
from typing import cast

from click import ClickException
from httpx2 import Client
from pydantic import ValidationError
from scim2_client.engines.httpx2 import SyncSCIMClient
from scim2_models import ListResponse
from scim2_models import Resource
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ScimProvider
from scim2_models import ScimProviderError
from scim2_models import ServiceProviderConfig

from scim2_cli.utils import SCIM_EXCEPTIONS
from scim2_cli.utils import command_name
from scim2_cli.utils import escape_control_characters
from scim2_cli.utils import exception_to_click_error

ResourceT = TypeVar("ResourceT", bound=Resource[Any])
T = TypeVar("T")


LIST_RESPONSE_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"


def error_details(exc: Exception) -> str:
    """Describe why the content of a file is invalid."""
    if not isinstance(exc, ValidationError):
        return str(exc)
    return "\n".join(
        f"{'.'.join(str(part) for part in error['loc']) or 'root'}: {error['msg']}"
        for error in exc.errors(include_url=False)
    )


def load_file(fd: IO[str], load: Callable[[Any], T]) -> T:
    """Read a configuration file, and fail with a readable error if its content is invalid."""
    try:
        return load(json.load(fd))
    except (ValueError, RecursionError) as exc:
        raise ClickException(
            escape_control_characters(f"Invalid file {fd.name}.\n{error_details(exc)}")
        ) from exc


def load_objects(payload: Any, model: type[ResourceT]) -> list[ResourceT]:
    """Read a list of objects, bare or wrapped in a ListResponse."""
    if isinstance(payload, list):
        return [model.model_validate(item) for item in payload]
    schemas = payload.get("schemas") if isinstance(payload, dict) else None
    if not isinstance(schemas, list) or LIST_RESPONSE_SCHEMA not in schemas:
        raise ValueError("Expected a list of objects, or a ListResponse.")
    list_response: ListResponse[ResourceT] = cast(Any, ListResponse)[
        model
    ].model_validate(payload)
    return list_response.resources or []


def describe_server(
    scim_client: SyncSCIMClient,
    schemas_fd: IO[str] | None,
    resource_types_fd: IO[str] | None,
    service_provider_config_fd: IO[str] | None,
) -> ScimProvider:
    """Describe the server with the configuration files, and query it for the others.

    The files are read before any request, so an invalid file is reported even
    when the server cannot be reached.
    """
    resource_types = (
        load_file(resource_types_fd, partial(load_objects, model=ResourceType))
        if resource_types_fd
        else None
    )
    schemas = (
        load_file(schemas_fd, partial(load_objects, model=Schema))
        if schemas_fd
        else None
    )
    config = (
        load_file(service_provider_config_fd, ServiceProviderConfig.model_validate)
        if service_provider_config_fd
        else None
    )
    if resource_types is None:
        response = cast("ListResponse[ResourceType]", scim_client.query(ResourceType))
        resource_types = response.resources or []
    if schemas is None:
        schemas = (
            cast("ListResponse[Schema]", scim_client.query(Schema)).resources or []
        )
    if config is None:
        config = cast(ServiceProviderConfig, scim_client.query(ServiceProviderConfig))
    return ScimProvider.from_discovery(schemas, resource_types, config)


class Session:
    """What the commands share: the server, discovered on first use, and the standard input."""

    def __init__(
        self,
        url: str | None,
        headers: dict[str, str],
        verify: bool,
        schemas: IO[str] | None,
        resource_types: IO[str] | None,
        service_provider_config: IO[str] | None,
    ) -> None:
        self.url = url
        self.headers = headers
        self.verify = verify
        self.schemas = schemas
        self.resource_types_file = resource_types
        self.service_provider_config = service_provider_config

    @cached_property
    def client(self) -> SyncSCIMClient:
        """The client of the server, described by the configuration files and the discovery."""
        if not self.url:
            raise ClickException("No SCIM server URL defined.")

        client = SyncSCIMClient(
            Client(base_url=self.url, headers=self.headers, verify=self.verify)
        )
        try:
            client.provider = describe_server(
                client,
                self.schemas,
                self.resource_types_file,
                self.service_provider_config,
            )
        except (*SCIM_EXCEPTIONS, ScimProviderError) as exc:
            error = exception_to_click_error(exc)
            raise ClickException(
                f"Could not discover the server at {escape_control_characters(self.url)}: "
                f"{error.message}"
            ) from exc
        return client

    @cached_property
    def resource_types(self) -> dict[str, ResourceType]:
        """The resource types of the server, by command name."""
        return {
            command_name(resource_type): resource_type
            for resource_type in self.client.provider.resource_types
            if resource_type.name or resource_type.id
        }

    @cached_property
    def stdin(self) -> Any:
        """The JSON payload passed to the standard input, if any."""
        if sys.stdin.isatty():  # pragma: no cover
            return None

        payload = sys.stdin.read().strip()
        if not payload:
            return None

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ClickException(f"Invalid JSON input.\n{exc}") from exc
