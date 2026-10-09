import json
import sys
from functools import cached_property
from typing import IO
from typing import Any
from typing import TypeVar
from typing import cast

from click import ClickException
from httpx2 import Client
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


def load_objects(fd: IO[str], model: type[ResourceT]) -> list[ResourceT]:
    """Read a list of objects, bare or wrapped in a ListResponse, from a JSON file."""
    payload = json.load(fd)
    if isinstance(payload, dict):
        list_response: ListResponse[ResourceT] = cast(Any, ListResponse)[
            model
        ].model_validate(payload)
        return list_response.resources or []
    return [model.model_validate(item) for item in payload]


def describe_server(
    scim_client: SyncSCIMClient,
    schemas_fd: IO[str] | None,
    resource_types_fd: IO[str] | None,
    service_provider_config_fd: IO[str] | None,
) -> ScimProvider:
    """Describe the server with the configuration files, and query it for the others."""
    resource_types = (
        load_objects(resource_types_fd, ResourceType)
        if resource_types_fd
        else cast(
            "ListResponse[ResourceType]", scim_client.query(ResourceType)
        ).resources
        or []
    )
    schemas = (
        load_objects(schemas_fd, Schema)
        if schemas_fd
        else cast("ListResponse[Schema]", scim_client.query(Schema)).resources or []
    )
    config = (
        ServiceProviderConfig.model_validate(json.load(service_provider_config_fd))
        if service_provider_config_fd
        else cast(ServiceProviderConfig, scim_client.query(ServiceProviderConfig))
    )
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
