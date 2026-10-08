import json

import pytest
from scim2_models import ResourceType

from scim2_cli import cli

USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
USERS = ResourceType(id="User", name="User", endpoint="/Users", schema_=USER_SCHEMA)
EMPLOYEES = ResourceType(
    id="Employee", name="Employee", endpoint="/Employees", schema_=USER_SCHEMA
)


@pytest.fixture
def invoke(runner, httpserver, tmp_path):
    """Invoke the CLI on a server describing the given resource types."""

    def wrapped(resource_types, *arguments, **kwargs):
        path = tmp_path / "resource_types.json"
        path.write_text(json.dumps([rt.model_dump() for rt in resource_types]))
        return runner.invoke(
            cli,
            ["--url", httpserver.url_for("/"), "--resource-types", path, *arguments],
            **kwargs,
        )

    return wrapped


@pytest.fixture
def employee(httpserver, simple_user_payload):
    payload = simple_user_payload("1")
    payload["meta"]["resourceType"] = "Employee"
    payload["meta"]["location"] = httpserver.url_for("/Employees/1")
    return payload


def respond(httpserver, path, method, payload, status=200):
    httpserver.expect_request(path, method=method).respond_with_json(
        payload, status=status, content_type="application/scim+json"
    )


def test_query_reaches_a_resource_type_sharing_a_schema(invoke, httpserver, employee):
    """Two resource types serving the same schema each have their own command."""
    respond(httpserver, "/Employees/1", "GET", employee)

    result = invoke([USERS, EMPLOYEES], "query", "employee", "1")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["meta"]["resourceType"] == "Employee"


def test_create_reaches_a_resource_type_sharing_a_schema(invoke, httpserver, employee):
    """A creation is sent to the endpoint of the resource type of the subcommand."""
    respond(httpserver, "/Employees", "POST", employee, status=201)

    result = invoke(
        [USERS, EMPLOYEES], "create", "employee", "--user-name", "1@example.com"
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "1"


def test_create_from_stdin_reaches_the_resource_type_of_the_subcommand(
    invoke, httpserver, employee
):
    """A payload passed to stdin is sent to the resource type of the subcommand."""
    respond(httpserver, "/Employees", "POST", employee, status=201)

    result = invoke(
        [USERS, EMPLOYEES],
        "create",
        "employee",
        input=json.dumps(
            {"schemas": [USER_SCHEMA], "userName": "1@example.com"},
        ),
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "1"


def test_replace_reaches_a_resource_type_sharing_a_schema(invoke, httpserver, employee):
    """A replacement is sent to the endpoint of the resource type of the subcommand."""
    respond(httpserver, "/Employees/1", "PUT", employee)

    result = invoke(
        [USERS, EMPLOYEES],
        "replace",
        "employee",
        "--id",
        "1",
        "--user-name",
        "1@example.com",
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "1"


def test_delete_reaches_a_resource_type_sharing_a_schema(invoke, httpserver):
    """A deletion is sent to the endpoint of the resource type."""
    httpserver.expect_request("/Employees/1", method="DELETE").respond_with_data(
        status=204
    )

    result = invoke([USERS, EMPLOYEES], "delete", "employee", "1")

    assert result.exit_code == 0, result.output


def test_subcommands_are_named_after_the_resource_types(invoke):
    """Each resource type has its subcommand, even when they share a schema."""
    result = invoke([USERS, EMPLOYEES], "create", "--help")

    assert result.exit_code == 0, result.output
    assert "employee" in result.output
    assert "user" in result.output


def test_resource_type_not_named_after_its_schema(invoke, httpserver, employee):
    """A resource type is reached even when none is named after its schema."""
    respond(httpserver, "/Employees/1", "GET", employee)

    result = invoke([EMPLOYEES], "query", "employee", "1")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "1"


@pytest.mark.parametrize("command", ["query", "delete"])
def test_resource_type_argument_ignores_the_case(invoke, httpserver, employee, command):
    """The resource type can be typed with any case."""
    respond(httpserver, "/Employees/1", "GET", employee)
    httpserver.expect_request("/Employees/1", method="DELETE").respond_with_data(
        status=204
    )

    result = invoke([USERS, EMPLOYEES], command, "EMPLOYEE", "1")

    assert result.exit_code == 0, result.output


@pytest.mark.parametrize("command", ["create", "replace"])
def test_subcommand_ignores_the_case(invoke, command):
    """The resource type subcommands can be typed with any case."""
    result = invoke([USERS, EMPLOYEES], command, "Employee", "--help")

    assert result.exit_code == 0, result.output
    assert "--user-name" in result.output


def test_resource_types_with_the_same_name_are_refused(invoke):
    """Two resource types with the same name cannot be told apart."""
    other = EMPLOYEES.model_copy(update={"id": "Other", "name": "user"})

    result = invoke([USERS, other], "query")

    assert result.exit_code == 1, result.output
    assert "Two resource types share the name user" in result.output


def test_resource_type_without_name_is_named_after_its_id(invoke, httpserver, employee):
    """A resource type without a name has a command named after its id."""
    nameless = EMPLOYEES.model_copy(update={"name": None})
    respond(httpserver, "/Employees/1", "GET", employee)

    result = invoke([USERS, nameless], "query", "employee", "1")

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["id"] == "1"


def test_resource_type_without_name_nor_id_has_no_command(invoke):
    """A resource type without a name nor an id cannot be designated."""
    anonymous = EMPLOYEES.model_copy(update={"name": None, "id": None})

    result = invoke([USERS, anonymous], "create", "--help")

    assert result.exit_code == 0, result.output
    assert "employee" not in result.output.lower()


def test_discovery_endpoint_wins_over_a_resource_type_of_the_same_name(invoke):
    """Query schema reads the schemas, even if a resource type is named Schema."""
    named_schema = EMPLOYEES.model_copy(update={"name": "Schema"})

    result = invoke([USERS, named_schema], "query", "schema")

    assert result.exit_code == 0, result.output
    assert "urn:ietf:params:scim:api:messages:2.0:ListResponse" in result.output
