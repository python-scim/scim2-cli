import json

import pytest
from scim2_models import Attribute
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ServiceProviderConfig

from scim2_cli import cli

THING_SCHEMA = "urn:example:schemas:Thing"


@pytest.fixture
def thing_server(httpserver, tmp_path):
    """Describe a server whose resources have attributes named after command options."""
    schema = Schema(
        id=THING_SCHEMA,
        name="Thing",
        attributes=[
            Attribute(name="me", type="string"),
            Attribute(name="indent", type="string"),
            Attribute(name="help", type="string"),
        ],
    )
    resource_type = ResourceType(
        id="Thing", name="Thing", endpoint="/Things", schema_=THING_SCHEMA
    )
    arguments = ["--url", httpserver.url_for("/")]
    for option, payload in {
        "--schemas": [schema.model_dump()],
        "--resource-types": [resource_type.model_dump()],
        "--service-provider-config": ServiceProviderConfig().model_dump(),
    }.items():
        path = tmp_path / f"{option.strip('-')}.json"
        path.write_text(json.dumps(payload))
        arguments += [option, str(path)]
    return arguments


@pytest.mark.parametrize("command", ["create", "replace"])
def test_attribute_options_do_not_collide_with_command_options(
    runner, thing_server, command
):
    """Attributes named after an option of the command get their own option."""
    result = runner.invoke(cli, [*thing_server, command, "thing", "--help"])

    assert result.exit_code == 0, result.output
    assert "--me-attribute TEXT" in result.output
    assert "--indent-attribute TEXT" in result.output
    assert "--help-attribute TEXT" in result.output


@pytest.mark.parametrize("endpoint", ["/Things", "/Me"])
def test_renamed_attribute_options_fill_the_attributes(
    runner, httpserver, thing_server, endpoint
):
    """The renamed options fill their attributes, next to the command options."""
    payload = {"schemas": [THING_SCHEMA], "me": "a", "indent": "b", "help": "c"}
    httpserver.expect_request(endpoint, method="POST", json=payload).respond_with_json(
        {**payload, "id": "1"}, status=201, content_type="application/scim+json"
    )
    me = ["--me"] if endpoint == "/Me" else []

    result = runner.invoke(
        cli,
        [
            *thing_server,
            "create",
            "thing",
            *me,
            "--no-indent",
            "--me-attribute",
            "a",
            "--indent-attribute",
            "b",
            "--help-attribute",
            "c",
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(result.output.splitlines()) == 1
    assert json.loads(result.output) == {**payload, "id": "1"}
