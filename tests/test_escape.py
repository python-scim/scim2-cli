import json
from unittest.mock import patch

import pytest
from scim2_models import Attribute
from scim2_models import ResourceType
from scim2_models import Schema
from scim2_models import ServiceProviderConfig
from scim2_tester import CheckResult
from scim2_tester import Status

from scim2_cli import cli

HOSTILE_SEQUENCES = [
    pytest.param("\x1b[1A\x1b[2K", "\\x1b[1A\\x1b[2K", id="csi"),
    pytest.param("\x1b]0;title\x1b\\", "\\x1b]0;title\\x1b\\", id="osc"),
    pytest.param("\x9b31m", "\\x9b31m", id="c1-csi"),
    pytest.param("\r", "\\r", id="carriage-return"),
    pytest.param("\x7f", "\\x7f", id="delete"),
    pytest.param("\u202e", "\\u202e", id="bidi-override"),
    pytest.param("\u2066", "\\u2066", id="bidi-isolate"),
]


def hostile_configuration(tmp_path, sequence):
    """Write the description of a server whose schema carries the sequence."""
    schema = Schema(
        id="urn:example:schemas:Hostile",
        name=f"Hostile{sequence}",
        attributes=[
            Attribute(name="nickName", type="string", description=f"nick{sequence}"),
            Attribute(name="title", type="string"),
            Attribute(
                name="badge",
                type="complex",
                description=f"badge{sequence}",
                sub_attributes=[
                    Attribute(
                        name="label", type="string", description=f"label{sequence}"
                    )
                ],
            ),
        ],
    )
    resource_type = ResourceType(
        id="Hostile",
        name="Hostile",
        endpoint="/Hostiles",
        schema_="urn:example:schemas:Hostile",
    )
    paths = {
        "--schemas": [schema.model_dump()],
        "--resource-types": [resource_type.model_dump()],
        "--service-provider-config": ServiceProviderConfig().model_dump(),
    }
    arguments = ["--url", "https://scim.example"]
    for option, payload in paths.items():
        path = tmp_path / f"{option.strip('-')}.json"
        path.write_text(json.dumps(payload))
        arguments += [option, str(path)]
    return arguments


@pytest.mark.parametrize("field", ["title", "reason", "data"])
@pytest.mark.parametrize(("sequence", "escaped"), HOSTILE_SEQUENCES)
def test_compliance_report_is_escaped(runner, httpserver, field, sequence, escaped):
    """The server cannot rewrite the compliance report on the terminal."""
    result = CheckResult(
        status=Status.ERROR, title="object_creation", reason="failed", data="payload"
    )
    setattr(result, field, f"{getattr(result, field)}{sequence}")

    with patch("scim2_cli.test.check_server", side_effect=[[result]]):
        output = runner.invoke(
            cli, ["--url", httpserver.url_for("/"), "test", "--verbose"], color=True
        ).output

    assert escaped in output
    assert sequence not in output


@pytest.mark.parametrize(("sequence", "escaped"), HOSTILE_SEQUENCES)
def test_error_message_is_escaped(runner, httpserver, sequence, escaped):
    """What the server sends back in an unexpected response is escaped in the error message."""
    httpserver.expect_request("/Users/1").respond_with_json(
        {"schemas": [f"urn:example:schemas:Unknown{sequence}"], "id": "1"},
        content_type="application/scim+json",
    )

    result = runner.invoke(
        cli, ["--url", httpserver.url_for("/"), "query", "user", "1"], color=True
    )

    assert result.exit_code == 1
    assert escaped in result.output
    assert sequence not in result.output


@pytest.mark.parametrize("command", ["create", "replace", "query", "delete"])
@pytest.mark.parametrize(("sequence", "escaped"), HOSTILE_SEQUENCES)
def test_subcommand_names_are_escaped(runner, tmp_path, command, sequence, escaped):
    """A schema name is listed escaped among the subcommands."""
    arguments = hostile_configuration(tmp_path, sequence)
    arguments += (
        [command, "--help"]
        if command in ("create", "replace")
        else [
            command,
            "unknown",
            "1",
        ]
    )

    output = runner.invoke(cli, arguments, color=True).output

    assert f"hostile{escaped.lower()}" in output
    assert sequence not in output


@pytest.mark.parametrize("command", ["create", "replace"])
@pytest.mark.parametrize(("sequence", "escaped"), HOSTILE_SEQUENCES)
def test_attribute_descriptions_are_escaped(
    runner, tmp_path, command, sequence, escaped
):
    """The schema descriptions shown as option help are escaped."""
    arguments = hostile_configuration(tmp_path, sequence)

    output = runner.invoke(
        cli, [*arguments, command, f"hostile{escaped.lower()}", "--help"], color=True
    ).output

    assert f"nick{escaped}" in output
    assert f"badge{escaped}" in output
    assert "--title TEXT" in output
    assert sequence not in output


def test_line_breaks_and_tabulations_are_kept(runner, httpserver):
    """Line breaks and tabulations are the layout of the messages, not escape sequences."""
    result = CheckResult(status=Status.ERROR, title="check", reason="first\n\tsecond")

    with patch("scim2_cli.test.check_server", side_effect=[[result]]):
        output = runner.invoke(
            cli, ["--url", httpserver.url_for("/"), "test"], color=True
        ).output

    assert "first\n\tsecond" in output
