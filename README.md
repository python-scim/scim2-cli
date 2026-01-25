# scim2-cli

An utility command line to help you perform requests against a SCIM server, while validating input and response payloads. It also uses [scim2-tester](https://scim2-tester.readthedocs.io) to perform a [SCIM server compliance test](https://scim2-cli.readthedocs.io/en/latest/reference.html#scim-url-test).

## What's SCIM anyway?

SCIM stands for System for Cross-domain Identity Management, and it is a provisioning protocol.
Provisioning is the action of managing a set of resources across different services, usually users and groups.
SCIM is often used between Identity Providers and applications in completion of standards like OAuth2 and OpenID Connect.
It allows users and groups creations, modifications and deletions to be synchronized between applications.

## Features

- **CRUD Commands**: `create`, `query`, `replace` and `delete` resources from the command line
- **Search Command**: Query resources using SCIM filters, sorting and pagination
- **Compliance Testing**: Built-in `test` command using [scim2-tester](https://scim2-tester.readthedocs.io) to validate server RFC compliance
- **Server Discovery**: Automatic retrieval of server schemas and resource types
- **Dynamic CLI Options**: Command options generated from server schemas
- **Flexible Input**: Pass attributes as CLI options or pipe JSON payloads via stdin
- **JSON Output**: Formatted JSON responses with optional indentation control
- **Authentication**: Custom HTTP headers support for Bearer tokens and other auth methods

## Installation

### Binary files

Binary files are available on the [releases page](https://github.com/python-scim/scim2-cli/releases).

### Python package

scim2-cli is published on the [PyPI repository](https://pypi.org/project/scim2-cli).
You can install it with your favourite python package manager.

```shell
pip install scim2-cli
```

### From sources

To run scim2-cli from the sources, [uv is needed](https://docs.astral.sh/uv/getting-started/installation/) for development:

```shell
git clone https://github.com/python-scim/scim2-cli.git
cd scim2-cli
uv sync
```

Then, it can be launched directly as a Python script:

```shell
uv run scim2 --help
```

Or you can build a single file binary from the sources:

```shell
uv sync --group bundle
uv run pyinstaller --name scim2 --onefile scim2_cli/__init__.py
./dist/scim2 --help
```

## Usage

Check the [reference](https://scim2-cli.readthedocs.io/en/latest/reference.html) for more details.

Here is an example of resource creation:

```shell
$ scim2 --url https://auth.example --header "Authorization: Bearer 12345" create user --user-name "bjensen@example.com"
{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "id": "2819c223-7f76-453a-919d-413861904646",
    "userName": "bjensen@example.com",
    "meta": {
        "resourceType": "User",
        "created": "2010-01-23T04:56:22Z",
        "lastModified": "2011-05-13T04:42:34Z",
        "version": 'W\\/"3694e05e9dff590"',
        "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
    },
}
```

Here is an example of resource query:

```shell
$ scim2 --url https://auth.example --header "Authorization: Bearer 12345" query user 2819c223-7f76-453a-919d-413861904646
{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "id": "2819c223-7f76-453a-919d-413861904646",
    "userName": "bjensen@example.com",
    "meta": {
        "resourceType": "User",
        "created": "2010-01-23T04:56:22Z",
        "lastModified": "2011-05-13T04:42:34Z",
        "version": 'W\\/"3694e05e9dff590"',
        "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
   }
}
```

scim2-cli belongs in a collection of SCIM tools developed by [Yaal Coop](https://yaal.coop),
with [scim2-models](https://github.com/python-scim/scim2-models),
[scim2-client](https://github.com/python-scim/scim2-client) and
[scim2-tester](https://github.com/python-scim/scim2-tester)
